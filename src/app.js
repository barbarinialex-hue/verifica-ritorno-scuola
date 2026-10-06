import { pool } from './db.js';
import { AppError } from './errors.js';

const VALID_STATUSES = new Set([
  'Inviata',
  'Approvata',
  'Presa in carico',
  'Inclusa nel dossier',
  'Risolta',
]);

function getNumeric(value, fieldName, { min, max, allowZero = false } = {}) {
  const normalized = Number(value);

  if (!Number.isFinite(normalized)) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} deve essere un numero valido.`);
  }

  if (min !== undefined && normalized < min) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} deve essere maggiore o uguale a ${min}.`);
  }

  if (max !== undefined && normalized > max) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} deve essere minore o uguale a ${max}.`);
  }

  if (!allowZero && normalized === 0) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} non può essere zero.`);
  }

  return normalized;
}

function getText(value, fieldName, { minLength = 1, maxLength = 4000 } = {}) {
  const normalized = String(value ?? '').trim();

  if (normalized.length < minLength) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} è obbligatorio.`);
  }

  if (normalized.length > maxLength) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} supera la lunghezza massima consentita.`);
  }

  return normalized;
}

function getOptionalId(value, fieldName) {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  const numeric = Number(value);
  if (!Number.isInteger(numeric) || numeric <= 0) {
    throw new AppError(400, 'VALIDATION_ERROR', `${fieldName} deve essere un ID valido.`);
  }

  return numeric;
}

function pick(body, keys) {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(body, key)) {
      return body[key];
    }
  }

  return undefined;
}

function serializeSegnalazione(row) {
  return {
    id: row.id,
    titolo: row.titolo,
    descrizioneTestuale: row.descrizione_testuale,
    latitudine: Number(row.latitudine),
    longitudine: Number(row.longitudine),
    indirizzo: row.indirizzo,
    statoAttuale: row.stato_attuale,
    dataCreazione: row.data_creazione,
    autoreId: row.fk_utente_autore,
    categoriaId: row.fk_categoria,
    quartiereId: row.fk_quartiere,
    segnalazionePadreId: row.fk_segnalazione_padre,
    categoriaNome: row.categoria_nome ?? null,
    quartiereNome: row.quartiere_nome ?? null,
    autoreNome: row.autore_nome ?? null,
    autoreCognome: row.autore_cognome ?? null,
  };
}

async function ensureReferenceExists(tableName, value, fieldName) {
  if (value === null || value === undefined) {
    return;
  }

  const result = await pool.query(`SELECT id FROM ${tableName} WHERE id = $1;`, [value]);
  if (result.rowCount === 0) {
    throw new AppError(400, 'INVALID_REFERENCE', `${fieldName} non esiste nel sistema.`);
  }
}

export async function listSegnalazioni(filters = {}) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const { categoriaId, quartiereId, stato, utenteId, limit = 50 } = filters;
  const params = [];
  const clauses = [];

  if (categoriaId !== undefined && categoriaId !== null && categoriaId !== '') {
    params.push(Number(categoriaId));
    clauses.push(`s.fk_categoria = $${params.length}`);
  }

  if (quartiereId !== undefined && quartiereId !== null && quartiereId !== '') {
    params.push(Number(quartiereId));
    clauses.push(`s.fk_quartiere = $${params.length}`);
  }

  if (stato) {
    params.push(String(stato));
    clauses.push(`s.stato_attuale = $${params.length}`);
  }

  if (utenteId !== undefined && utenteId !== null && utenteId !== '') {
    params.push(Number(utenteId));
    clauses.push(`s.fk_utente_autore = $${params.length}`);
  }

  const safeLimit = Math.min(Math.max(Number(limit) || 50, 1), 200);
  params.push(safeLimit);

  const whereClause = clauses.length > 0 ? `WHERE ${clauses.join(' AND ')}` : '';

  const result = await pool.query(
    `SELECT
       s.*,
       c.nome_categoria AS categoria_nome,
       q.nome_quartiere AS quartiere_nome,
       u.nome AS autore_nome,
       u.cognome AS autore_cognome
     FROM segnalazione s
     LEFT JOIN categoria c ON c.id = s.fk_categoria
     LEFT JOIN quartiere q ON q.id = s.fk_quartiere
     LEFT JOIN utente u ON u.id = s.fk_utente_autore
     ${whereClause}
     ORDER BY s.data_creazione DESC
     LIMIT $${params.length};`,
    params
  );

  return result.rows.map(serializeSegnalazione);
}

export async function getSegnalazioneById(id) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const numericId = getNumeric(id, 'ID segnalazione', { min: 1, allowZero: false });

  const result = await pool.query(
    `SELECT
       s.*,
       c.nome_categoria AS categoria_nome,
       q.nome_quartiere AS quartiere_nome,
       u.nome AS autore_nome,
       u.cognome AS autore_cognome
     FROM segnalazione s
     LEFT JOIN categoria c ON c.id = s.fk_categoria
     LEFT JOIN quartiere q ON q.id = s.fk_quartiere
     LEFT JOIN utente u ON u.id = s.fk_utente_autore
     WHERE s.id = $1;`,
    [numericId]
  );

  if (result.rowCount === 0) {
    throw new AppError(404, 'NOT_FOUND', 'Segnalazione non trovata.');
  }

  return serializeSegnalazione(result.rows[0]);
}

export async function createSegnalazione(input, user) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  if (!user || !user.id) {
    throw new AppError(401, 'AUTH_REQUIRED', 'Autenticazione richiesta per creare una segnalazione.');
  }

  const body = input ?? {};
  const titolo = getText(pick(body, ['titolo']), 'Titolo', { maxLength: 160 });
  const descrizioneTestuale = getText(pick(body, ['descrizioneTestuale', 'descrizione_testuale']), 'Descrizione', { maxLength: 5000 });
  const latitudine = getNumeric(pick(body, ['latitudine']), 'Latitudine', { min: -90, max: 90 });
  const longitudine = getNumeric(pick(body, ['longitudine']), 'Longitudine', { min: -180, max: 180 });
  const indirizzo = getText(pick(body, ['indirizzo']), 'Indirizzo', { maxLength: 200 });
  const categoriaId = getNumeric(pick(body, ['categoriaId', 'fkCategoria']), 'Categoria', { min: 1, allowZero: false });
  const quartiereId = getNumeric(pick(body, ['quartiereId', 'fkQuartiere']), 'Quartiere', { min: 1, allowZero: false });
  const segnalazionePadreId = getOptionalId(pick(body, ['segnalazionePadreId', 'fkSegnalazionePadre']), 'Segnalazione padre');
  const statoAttuale = String(pick(body, ['statoAttuale', 'stato_attuale']) ?? 'Inviata').trim();

  if (!VALID_STATUSES.has(statoAttuale)) {
    throw new AppError(400, 'VALIDATION_ERROR', 'Stato non valido.');
  }

  await ensureReferenceExists('categoria', categoriaId, 'Categoria');
  await ensureReferenceExists('quartiere', quartiereId, 'Quartiere');
  if (segnalazionePadreId !== null) {
    await ensureReferenceExists('segnalazione', segnalazionePadreId, 'Segnalazione padre');
  }

  const result = await pool.query(
    `INSERT INTO segnalazione (
       titolo,
       descrizione_testuale,
       latitudine,
       longitudine,
       indirizzo,
       data_creazione,
       stato_attuale,
       fk_utente_autore,
       fk_categoria,
       fk_quartiere,
       fk_segnalazione_padre
     ) VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7, $8, $9, $10)
     RETURNING *;`,
    [titolo, descrizioneTestuale, latitudine, longitudine, indirizzo, statoAttuale, user.id, categoriaId, quartiereId, segnalazionePadreId]
  );

  return getSegnalazioneById(result.rows[0].id);
}

export async function updateSegnalazione(id, input, user) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const existing = await getSegnalazioneById(id);

  if (user.id !== existing.autoreId && !['MembroComitato', 'Admin'].includes(user.tipoRuolo)) {
    throw new AppError(403, 'FORBIDDEN', 'Non hai il permesso di modificare questa segnalazione.');
  }

  const body = input ?? {};
  const updates = [];
  const params = [];

  const title = pick(body, ['titolo']);
  const description = pick(body, ['descrizioneTestuale', 'descrizione_testuale']);
  const latitude = pick(body, ['latitudine']);
  const longitude = pick(body, ['longitudine']);
  const address = pick(body, ['indirizzo']);
  const categoryId = pick(body, ['categoriaId', 'fkCategoria']);
  const quarterId = pick(body, ['quartiereId', 'fkQuartiere']);
  const parentId = pick(body, ['segnalazionePadreId', 'fkSegnalazionePadre']);
  const status = pick(body, ['statoAttuale', 'stato_attuale']);

  if (title !== undefined) {
    updates.push('titolo = $' + (params.length + 1));
    params.push(getText(title, 'Titolo', { maxLength: 160 }));
  }

  if (description !== undefined) {
    updates.push('descrizione_testuale = $' + (params.length + 1));
    params.push(getText(description, 'Descrizione', { maxLength: 5000 }));
  }

  if (latitude !== undefined) {
    updates.push('latitudine = $' + (params.length + 1));
    params.push(getNumeric(latitude, 'Latitudine', { min: -90, max: 90 }));
  }

  if (longitude !== undefined) {
    updates.push('longitudine = $' + (params.length + 1));
    params.push(getNumeric(longitude, 'Longitudine', { min: -180, max: 180 }));
  }

  if (address !== undefined) {
    updates.push('indirizzo = $' + (params.length + 1));
    params.push(getText(address, 'Indirizzo', { maxLength: 200 }));
  }

  if (categoryId !== undefined) {
    const numericCategoryId = getNumeric(categoryId, 'Categoria', { min: 1, allowZero: false });
    await ensureReferenceExists('categoria', numericCategoryId, 'Categoria');
    updates.push('fk_categoria = $' + (params.length + 1));
    params.push(numericCategoryId);
  }

  if (quarterId !== undefined) {
    const numericQuartiereId = getNumeric(quarterId, 'Quartiere', { min: 1, allowZero: false });
    await ensureReferenceExists('quartiere', numericQuartiereId, 'Quartiere');
    updates.push('fk_quartiere = $' + (params.length + 1));
    params.push(numericQuartiereId);
  }

  if (parentId !== undefined && parentId !== null && parentId !== '') {
    const parentValue = getOptionalId(parentId, 'Segnalazione padre');
    if (parentValue !== null) {
      await ensureReferenceExists('segnalazione', parentValue, 'Segnalazione padre');
    }
    updates.push('fk_segnalazione_padre = $' + (params.length + 1));
    params.push(parentValue);
  }

  if (status !== undefined) {
    const normalizedStatus = String(status).trim();
    if (!VALID_STATUSES.has(normalizedStatus)) {
      throw new AppError(400, 'VALIDATION_ERROR', 'Stato non valido.');
    }
    updates.push('stato_attuale = $' + (params.length + 1));
    params.push(normalizedStatus);
  }

  if (updates.length === 0) {
    return existing;
  }

  params.push(id);
  const query = `UPDATE segnalazione SET ${updates.join(', ')} WHERE id = $${params.length} RETURNING *;`;
  const result = await pool.query(query, params);

  return getSegnalazioneById(result.rows[0].id);
}

export async function deleteSegnalazione(id, user) {
  if (!pool) {
    throw new AppError(503, 'DB_NOT_CONFIGURED', 'Database is not configured.');
  }

  const existing = await getSegnalazioneById(id);

  if (user.id !== existing.autoreId && !['MembroComitato', 'Admin'].includes(user.tipoRuolo)) {
    throw new AppError(403, 'FORBIDDEN', 'Non hai il permesso di eliminare questa segnalazione.');
  }

  await pool.query('DELETE FROM segnalazione WHERE id = $1;', [id]);
  return { deleted: true, id: existing.id };
}
