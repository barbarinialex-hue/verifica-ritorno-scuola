import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

import config from './config.js';
import { AppError } from './errors.js';
import { pool } from './db.js';

const VALID_ROLES = ['Cittadino', 'MembroComitato', 'Admin'];

function sanitizeUser(row) {
  if (!row) {
    return null;
  }

  return {
    id: row.id,
    nome: row.nome,
    cognome: row.cognome,
    email: row.email,
    tipoRuolo: row.tipo_ruolo,
    dataRegistrazione: row.data_registrazione,
    quartiereId: row.fk_quartiere,
  };
}

export function signToken(user) {
  return jwt.sign(
    {
      sub: String(user.id),
      email: user.email,
      role: user.tipoRuolo,
    },
    config.jwtSecret,
    { expiresIn: config.jwtExpiresIn }
  );
}

export function verifyToken(token) {
  return jwt.verify(token, config.jwtSecret);
}

export async function getUserById(userId) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const result = await pool.query(
    `SELECT id, nome, cognome, email, tipo_ruolo, data_registrazione, fk_quartiere
     FROM utente
     WHERE id = $1;`,
    [userId]
  );

  return sanitizeUser(result.rows[0] ?? null);
}

export async function registerUser({ nome, cognome, email, password, tipoRuolo, quartiereId }) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const safeNome = String(nome ?? '').trim();
  const safeCognome = String(cognome ?? '').trim();
  const safeEmail = String(email ?? '').trim().toLowerCase();
  const safePassword = String(password ?? '');
  const safeTipoRuolo = String(tipoRuolo ?? 'Cittadino').trim();
  const safeQuartiereId = Number(quartiereId ?? 0);

  if (!safeNome || !safeCognome || !safeEmail || !safePassword) {
    throw new AppError(400, 'VALIDATION_ERROR', 'Nome, cognome, email e password sono obbligatori.');
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(safeEmail)) {
    throw new AppError(400, 'VALIDATION_ERROR', 'Il campo email non è valido.');
  }

  if (safePassword.length < 8) {
    throw new AppError(400, 'VALIDATION_ERROR', 'La password deve contenere almeno 8 caratteri.');
  }

  if (!VALID_ROLES.includes(safeTipoRuolo)) {
    throw new AppError(400, 'VALIDATION_ERROR', 'Ruolo non valido. Ruoli supportati: Cittadino, MembroComitato, Admin.');
  }

  if (!Number.isInteger(safeQuartiereId) || safeQuartiereId <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', 'Il quartiere è obbligatorio e deve essere un ID valido.');
  }

  const existingUser = await pool.query('SELECT id FROM utente WHERE email = $1;', [safeEmail]);
  if (existingUser.rowCount > 0) {
    throw new AppError(409, 'EMAIL_EXISTS', 'Esiste già un account con questa email.');
  }

  const quartiereCheck = await pool.query('SELECT id FROM quartiere WHERE id = $1;', [safeQuartiereId]);
  if (quartiereCheck.rowCount === 0) {
    throw new AppError(400, 'INVALID_QUARTIERE', 'Il quartiere specificato non esiste.');
  }

  const passwordHash = await bcrypt.hash(safePassword, 10);

  const result = await pool.query(
    `INSERT INTO utente (nome, cognome, email, password_hash, tipo_ruolo, fk_quartiere)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING id, nome, cognome, email, tipo_ruolo, data_registrazione, fk_quartiere;`,
    [safeNome, safeCognome, safeEmail, passwordHash, safeTipoRuolo, safeQuartiereId]
  );

  return {
    user: sanitizeUser(result.rows[0]),
    token: signToken(sanitizeUser(result.rows[0])),
  };
}

export async function loginUser({ email, password }) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const safeEmail = String(email ?? '').trim().toLowerCase();
  const safePassword = String(password ?? '');

  if (!safeEmail || !safePassword) {
    throw new AppError(400, 'VALIDATION_ERROR', 'Email e password sono obbligatori.');
  }

  const result = await pool.query(
    `SELECT id, nome, cognome, email, password_hash, tipo_ruolo, data_registrazione, fk_quartiere
     FROM utente
     WHERE email = $1;`,
    [safeEmail]
  );

  const userRow = result.rows[0];
  if (!userRow) {
    throw new AppError(401, 'INVALID_CREDENTIALS', 'Credenziali non valide.');
  }

  const isValidPassword = await bcrypt.compare(safePassword, userRow.password_hash);
  if (!isValidPassword) {
    throw new AppError(401, 'INVALID_CREDENTIALS', 'Credenziali non valide.');
  }

  const user = sanitizeUser(userRow);

  return {
    user,
    token: signToken(user),
  };
}
