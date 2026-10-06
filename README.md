import test from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';

import app from '../src/app.js';
import { pool } from '../src/db.js';

const hasDatabaseConfig = Boolean(process.env.DATABASE_URL);

async function ensureSeedData() {
  const quartiereResult = await pool.query(
    `INSERT INTO quartiere (nome_quartiere, cap_zona)
     VALUES ('Quartiere Segnalazioni', '22222')
     ON CONFLICT (nome_quartiere, cap_zona) DO NOTHING
     RETURNING id;`
  );

  const quartiereId = quartiereResult.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM quartiere WHERE nome_quartiere = 'Quartiere Segnalazioni' AND cap_zona = '22222';`)
  ).rows[0].id;

  const categoriaResult = await pool.query(
    `INSERT INTO categoria (nome_categoria, descrizione)
     VALUES ('Illuminazione', 'Problemi legati alla luce pubblica e sicurezza stradale.')
     ON CONFLICT (nome_categoria) DO NOTHING
     RETURNING id;`
  );

  const categoriaId = categoriaResult.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM categoria WHERE nome_categoria = 'Illuminazione';`)
  ).rows[0].id;

  return { quartiereId, categoriaId };
}

async function registerUser(email = `segn.${Date.now()}@example.com`) {
  const seed = await ensureSeedData();
  const response = await request(app).post('/api/auth/register').send({
    nome: 'Marco',
    cognome: 'Bianchi',
    email,
    password: 'Password123!',
    tipoRuolo: 'Cittadino',
    quartiereId: seed.quartiereId,
  });

  return {
    response,
    token: response.body.token,
    quartiereId: seed.quartiereId,
    categoriaId: seed.categoriaId,
  };
}

test('POST /api/segnalazioni creates a valid report for an authenticated user', { skip: !hasDatabaseConfig }, async () => {
  const { token, quartiereId, categoriaId } = await registerUser();

  const response = await request(app)
    .post('/api/segnalazioni')
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Lampione guasto',
      descrizioneTestuale: 'Il lampione del viale principale non funziona da diversi giorni.',
      latitudine: 45.123456,
      longitudine: 9.123456,
      indirizzo: 'Via Roma 12',
      categoriaId,
      quartiereId,
    });

  assert.equal(response.status, 201);
  assert.equal(response.body.success, true);
  assert.equal(response.body.data.titolo, 'Lampione guasto');
  assert.equal(response.body.data.statoAttuale, 'Inviata');
});

test('GET /api/segnalazioni returns the list of reports', { skip: !hasDatabaseConfig }, async () => {
  const { token, quartiereId, categoriaId } = await registerUser();

  await request(app)
    .post('/api/segnalazioni')
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Buche in strada',
      descrizioneTestuale: 'Sono presenti diverse buche vicino alla scuola.',
      latitudine: 45.223456,
      longitudine: 9.223456,
      indirizzo: 'Via del Parco 22',
      categoriaId,
      quartiereId,
    });

  const response = await request(app).get('/api/segnalazioni');

  assert.equal(response.status, 200);
  assert.equal(response.body.success, true);
  assert.ok(Array.isArray(response.body.data));
  assert.ok(response.body.data.some((item) => item.titolo === 'Buche in strada'));
});

test('PATCH /api/segnalazioni/:id updates the report and preserves ownership rules', { skip: !hasDatabaseConfig }, async () => {
  const { token, quartiereId, categoriaId } = await registerUser();

  const created = await request(app)
    .post('/api/segnalazioni')
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Manca la segnaletica',
      descrizioneTestuale: 'Non c’è segnaletica stradale vicino al passaggio pedonale.',
      latitudine: 45.323456,
      longitudine: 9.323456,
      indirizzo: 'Piazza della Vittoria 1',
      categoriaId,
      quartiereId,
    });

  const response = await request(app)
    .patch(`/api/segnalazioni/${created.body.data.id}`)
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Manca la segnaletica stradale',
      statoAttuale: 'Approvata',
    });

  assert.equal(response.status, 200);
  assert.equal(response.body.success, true);
  assert.equal(response.body.data.titolo, 'Manca la segnaletica stradale');
  assert.equal(response.body.data.statoAttuale, 'Approvata');
});

test('DELETE /api/segnalazioni/:id removes a report created by the user', { skip: !hasDatabaseConfig }, async () => {
  const { token, quartiereId, categoriaId } = await registerUser();

  const created = await request(app)
    .post('/api/segnalazioni')
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Panchina rotta',
      descrizioneTestuale: 'La panchina nel parco è rotta e pericolosa.',
      latitudine: 45.423456,
      longitudine: 9.423456,
      indirizzo: 'Parco Sud 15',
      categoriaId,
      quartiereId,
    });

  const response = await request(app)
    .delete(`/api/segnalazioni/${created.body.data.id}`)
    .set('Authorization', `Bearer ${token}`);

  assert.equal(response.status, 200);
  assert.equal(response.body.success, true);
  assert.equal(response.body.data.deleted, true);
});
