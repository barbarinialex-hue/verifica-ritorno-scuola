import test from 'node:test';
import assert from 'node:assert/strict';

import { initializeDatabase, pool } from '../src/db.js';

const hasDatabaseConfig = Boolean(process.env.DATABASE_URL);

test('initializeDatabase is not allowed without a configured DATABASE_URL', async () => {
  const originalDatabaseUrl = process.env.DATABASE_URL;

  delete process.env.DATABASE_URL;

  try {
    await assert.rejects(() => initializeDatabase(), {
      name: 'AppError',
      code: 'DB_NOT_CONFIGURED',
    });
  } finally {
    if (originalDatabaseUrl) {
      process.env.DATABASE_URL = originalDatabaseUrl;
    }
  }
});

test('database schema can be initialized when a database is configured', {
  skip: !hasDatabaseConfig,
}, async () => {
  const result = await initializeDatabase();

  assert.equal(result.status, 'ok');
  assert.match(result.message, /Database schema initialized successfully/i);

  const tables = await pool.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN (
        'quartiere',
        'utente',
        'categoria',
        'segnalazione',
        'allegato_multimediale',
        'sostegno',
        'dossier',
        'dossier_segnalazione'
      )
    ORDER BY table_name;
  `);

  assert.deepEqual(
    tables.rows.map((row) => row.table_name),
    [
      'allegato_multimediale',
      'categoria',
      'dossier',
      'dossier_segnalazione',
      'quartiere',
      'segnalazione',
      'sostegno',
      'utente',
    ]
  );

  const insertQuartiere = await pool.query(
    `INSERT INTO quartiere (nome_quartiere, cap_zona)
     VALUES ('Quartiere Test', '00100')
     ON CONFLICT (nome_quartiere, cap_zona) DO NOTHING
     RETURNING id;`
  );

  const quartiereId = insertQuartiere.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM quartiere WHERE nome_quartiere = 'Quartiere Test' AND cap_zona = '00100';`)
  ).rows[0].id;

  const insertCategoria = await pool.query(
    `INSERT INTO categoria (nome_categoria, descrizione)
     VALUES ('Buche stradali', 'Criticità relative alla viabilità urbana.')
     ON CONFLICT (nome_categoria) DO NOTHING
     RETURNING id;`
  );

  const categoriaId = insertCategoria.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM categoria WHERE nome_categoria = 'Buche stradali';`)
  ).rows[0].id;

  const insertUser = await pool.query(
    `INSERT INTO utente (nome, cognome, email, password_hash, tipo_ruolo, fk_quartiere)
     VALUES ('Mario', 'Rossi', 'mario.rossi.test@example.com', 'hashed_password', 'Cittadino', $1)
     ON CONFLICT (email) DO NOTHING
     RETURNING id;`,
    [quartiereId]
  );

  const userId = insertUser.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM utente WHERE email = 'mario.rossi.test@example.com';`)
  ).rows[0].id;

  const insertSegnalazione = await pool.query(
    `INSERT INTO segnalazione (
       titolo,
       descrizione_testuale,
       latitudine,
       longitudine,
       indirizzo,
       fk_utente_autore,
       fk_categoria,
       fk_quartiere
     ) VALUES (
       'Buche in via Test',
       'La strada presenta diverse buche e rischio per i pedoni.',
       45.123456,
       9.123456,
       'Via Test 1',
       $1,
       $2,
       $3
     ) RETURNING id;`,
    [userId, categoriaId, quartiereId]
  );

  const segnalazioneId = insertSegnalazione.rows[0].id;

  await pool.query(
    `INSERT INTO sostegno (fk_utente, fk_segnalazione)
     VALUES ($1, $2)
     ON CONFLICT (fk_utente, fk_segnalazione) DO NOTHING;`,
    [userId, segnalazioneId]
  );

  const supportCheck = await pool.query(
    `SELECT COUNT(*)::int AS count FROM sostegno WHERE fk_segnalazione = $1;`,
    [segnalazioneId]
  );

  assert.equal(supportCheck.rows[0].count, 1);
});
