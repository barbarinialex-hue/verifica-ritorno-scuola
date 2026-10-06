import { pool } from './db.js';
import { AppError } from './errors.js';

export async function getSupportSummary(segnalazioneId, userId = null) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const numericId = Number(segnalazioneId);
  if (!Number.isInteger(numericId) || numericId <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', 'ID segnalazione non valido.');
  }

  const segnalazioneCheck = await pool.query('SELECT id FROM segnalazione WHERE id = $1;', [numericId]);
  if (segnalazioneCheck.rowCount === 0) {
    throw new AppError(404, 'NOT_FOUND', 'Segnalazione non trovata.');
  }

  const supportResult = await pool.query(
    `SELECT COUNT(*)::int AS support_count
     FROM sostegno
     WHERE fk_segnalazione = $1;`,
    [numericId]
  );

  let hasSupported = false;
  if (userId !== null && userId !== undefined) {
    const userResult = await pool.query(
      `SELECT 1
       FROM sostegno
       WHERE fk_segnalazione = $1 AND fk_utente = $2;`,
      [numericId, userId]
    );
    hasSupported = userResult.rowCount > 0;
  }

  return {
    segnalazioneId: numericId,
    supportCount: supportResult.rows[0].support_count,
    hasSupported,
  };
}

export async function addSupport({ segnalazioneId, userId }) {
  if (!userId) {
    throw new AppError(401, 'AUTH_REQUIRED', 'Autenticazione richiesta per esprimere un sostegno.');
  }

  const numericId = Number(segnalazioneId);
  if (!Number.isInteger(numericId) || numericId <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', 'ID segnalazione non valido.');
  }

  const summary = await getSupportSummary(numericId, userId);
  if (summary.hasSupported) {
    return summary;
  }

  await pool.query(
    `INSERT INTO sostegno (fk_utente, fk_segnalazione, data_voto)
     VALUES ($1, $2, NOW())
     ON CONFLICT (fk_utente, fk_segnalazione) DO NOTHING;`,
    [userId, numericId]
  );

  return getSupportSummary(numericId, userId);
}

export async function removeSupport({ segnalazioneId, userId }) {
  if (!userId) {
    throw new AppError(401, 'AUTH_REQUIRED', 'Autenticazione richiesta per rimuovere un sostegno.');
  }

  const numericId = Number(segnalazioneId);
  if (!Number.isInteger(numericId) || numericId <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', 'ID segnalazione non valido.');
  }

  await pool.query(
    `DELETE FROM sostegno
     WHERE fk_segnalazione = $1 AND fk_utente = $2;`,
    [numericId, userId]
  );

  return getSupportSummary(numericId, userId);
}
