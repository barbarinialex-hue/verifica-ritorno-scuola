import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

import { pool } from './db.js';
import { AppError } from './errors.js';
import config from './config.js';

const ALLOWED_MIME_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/webp',
  'video/mp4',
  'video/quicktime',
  'video/webm',
]);

function toFileType(mimetype) {
  if (mimetype.startsWith('image/')) {
    return 'Foto';
  }

  if (mimetype.startsWith('video/')) {
    return 'Video';
  }

  throw new AppError(400, 'INVALID_FILE_TYPE', 'Tipo file non supportato. Inserire una foto o un video.');
}

function resolveExtension(originalName, mimetype) {
  const extension = path.extname(originalName || '').toLowerCase();
  if (extension) {
    return extension;
  }

  if (mimetype === 'image/jpeg') {
    return '.jpg';
  }

  if (mimetype === 'image/png') {
    return '.png';
  }

  if (mimetype === 'image/webp') {
    return '.webp';
  }

  if (mimetype === 'video/mp4') {
    return '.mp4';
  }

  if (mimetype === 'video/quicktime') {
    return '.mov';
  }

  if (mimetype === 'video/webm') {
    return '.webm';
  }

  return '.bin';
}

export async function ensureUploadDirectory() {
  await fs.mkdir(config.uploadDir, { recursive: true });
}

export async function listAttachmentsForSegnalazione(segnalazioneId) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const numericId = Number(segnalazioneId);
  if (!Number.isInteger(numericId) || numericId <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', 'ID segnalazione non valido.');
  }

  const result = await pool.query(
    `SELECT id, url_file, tipo_file, data_upload, fk_segnalazione
     FROM allegato_multimediale
     WHERE fk_segnalazione = $1
     ORDER BY data_upload DESC;`,
    [numericId]
  );

  return result.rows.map((row) => ({
    id: row.id,
    urlFile: row.url_file,
    tipoFile: row.tipo_file,
    dataUpload: row.data_upload,
    segnalazioneId: row.fk_segnalazione,
  }));
}

export async function createAttachment({ segnalazioneId, file, user }) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  if (!file || !file.buffer || !file.mimetype) {
    throw new AppError(400, 'UPLOAD_ERROR', 'Nessun file valido ricevuto.');
  }

  if (!ALLOWED_MIME_TYPES.has(file.mimetype)) {
    throw new AppError(400, 'INVALID_FILE_TYPE', 'Tipo file non supportato. Inserire una foto o un video.');
  }

  const numericId = Number(segnalazioneId);
  if (!Number.isInteger(numericId) || numericId <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', 'ID segnalazione non valido.');
  }

  const segnalazioneResult = await pool.query(
    `SELECT id, fk_utente_autore
     FROM segnalazione
     WHERE id = $1;`,
    [numericId]
  );

  if (segnalazioneResult.rowCount === 0) {
    throw new AppError(404, 'NOT_FOUND', 'Segnalazione non trovata.');
  }

  const isOwner = user.id === segnalazioneResult.rows[0].fk_utente_autore;
  const isModerator = ['MembroComitato', 'Admin'].includes(user.tipoRuolo);

  if (!isOwner && !isModerator) {
    throw new AppError(403, 'FORBIDDEN', 'Non hai il permesso di allegare file a questa segnalazione.');
  }

  await ensureUploadDirectory();

  const fileType = toFileType(file.mimetype);
  const extension = resolveExtension(file.originalname, file.mimetype);
  const uniqueName = `${Date.now()}-${crypto.randomUUID()}${extension}`;
  const destination = path.join(config.uploadDir, uniqueName);

  await fs.writeFile(destination, file.buffer);

  const urlFile = `/uploads/${uniqueName}`;
  const result = await pool.query(
    `INSERT INTO allegato_multimediale (url_file, tipo_file, data_upload, fk_segnalazione)
     VALUES ($1, $2, NOW(), $3)
     RETURNING id, url_file, tipo_file, data_upload, fk_segnalazione;`,
    [urlFile, fileType, numericId]
  );

  return {
    id: result.rows[0].id,
    urlFile: result.rows[0].url_file,
    tipoFile: result.rows[0].tipo_file,
    dataUpload: result.rows[0].data_upload,
    segnalazioneId: result.rows[0].fk_segnalazione,
  };
}
