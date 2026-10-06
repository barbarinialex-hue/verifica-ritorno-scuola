import test from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';

import app from '../src/app.js';
import { pool } from '../src/db.js';

const hasDatabaseConfig = Boolean(process.env.DATABASE_URL);

async function ensureSeedData() {
  const quartiereResult = await pool.query(
    `INSERT INTO quartiere (nome_quartiere, cap_zona)
     VALUES ('Quartiere Media', '33333')
     ON CONFLICT (nome_quartiere, cap_zona) DO NOTHING
     RETURNING id;`
  );

  const quartiereId = quartiereResult.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM quartiere WHERE nome_quartiere = 'Quartiere Media' AND cap_zona = '33333';`)
  ).rows[0].id;

  const categoriaResult = await pool.query(
    `INSERT INTO categoria (nome_categoria, descrizione)
     VALUES ('Verde pubblico', 'Problemi legati al verde, ai giardini e ai parchi.')
     ON CONFLICT (nome_categoria) DO NOTHING
     RETURNING id;`
  );

  const categoriaId = categoriaResult.rows[0]?.id ?? (
    await pool.query(`SELECT id FROM categoria WHERE nome_categoria = 'Verde pubblico';`)
  ).rows[0].id;

  return { quartiereId, categoriaId };
}

async function createAuthenticatedUser(email = `media.${Date.now()}@example.com`) {
  const seed = await ensureSeedData();
  const response = await request(app).post('/api/auth/register').send({
    nome: 'Sara',
    cognome: 'Luna',
    email,
    password: 'Password123!',
    tipoRuolo: 'Cittadino',
    quartiereId: seed.quartiereId,
  });

  return {
    token: response.body.token,
    quartiereId: seed.quartiereId,
    categoriaId: seed.categoriaId,
  };
}

test('POST /api/segnalazioni/:id/allegati accepts an image upload for the owner', { skip: !hasDatabaseConfig }, async () => {
  const { token, quartiereId, categoriaId } = await createAuthenticatedUser();

  const created = await request(app)
    .post('/api/segnalazioni')
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Albero caduto',
      descrizioneTestuale: 'Un albero si è abbattuto sul marciapiede e blocca il passaggio.',
      latitudine: 45.133456,
      longitudine: 9.133456,
      indirizzo: 'Viale dei Giardini 8',
      categoriaId,
      quartiereId,
    });

  const response = await request(app)
    .post(`/api/segnalazioni/${created.body.data.id}/allegati`)
    .set('Authorization', `Bearer ${token}`)
    .attach('file', Buffer.from('fake-image-payload'), {
      filename: 'albero.png',
      contentType: 'image/png',
    });

  assert.equal(response.status, 201);
  assert.equal(response.body.success, true);
  assert.equal(response.body.data.tipoFile, 'Foto');
  assert.match(response.body.data.urlFile, /^\/uploads\//);
});

test('POST /api/segnalazioni/:id/sostegno adds and toggles support state', { skip: !hasDatabaseConfig }, async () => {
  const { token, quartiereId, categoriaId } = await createAuthenticatedUser();

  const created = await request(app)
    .post('/api/segnalazioni')
    .set('Authorization', `Bearer ${token}`)
    .send({
      titolo: 'Pista ciclabile pericolosa',
      descrizioneTestuale: 'La pista ciclabile è ridotta e senza protezioni.',
      latitudine: 45.233456,
      longitudine: 9.233456,
      indirizzo: 'Corso Europa 44',
      categoriaId,
      quartiereId,
    });

  const supportResponse = await request(app)
    .post(`/api/segnalazioni/${created.body.data.id}/sostegno`)
    .set('Authorization', `Bearer ${token}`);

  assert.equal(supportResponse.status, 201);
  assert.equal(supportResponse.body.success, true);
  assert.equal(supportResponse.body.data.supportCount, 1);
  assert.equal(supportResponse.body.data.hasSupported, true);

  const summaryResponse = await request(app)
    .get(`/api/segnalazioni/${created.body.data.id}/sostegno`)
    .set('Authorization', `Bearer ${token}`);

  assert.equal(summaryResponse.status, 200);
  assert.equal(summaryResponse.body.data.supportCount, 1);
  assert.equal(summaryResponse.body.data.hasSupported, true);

  const removeResponse = await request(app)
    .delete(`/api/segnalazioni/${created.body.data.id}/sostegno`)
    .set('Authorization', `Bearer ${token}`);

  assert.equal(removeResponse.status, 200);
  assert.equal(removeResponse.body.data.supportCount, 0);
  assert.equal(removeResponse.body.data.hasSupported, false);
});
