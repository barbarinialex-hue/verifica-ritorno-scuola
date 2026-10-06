import test from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';

import app from '../src/app.js';

test('GET / returns a project-level status payload', async () => {
  const response = await request(app).get('/');

  assert.equal(response.status, 200);
  assert.equal(response.body.name, 'Verifica Ritorno Scuola');
  assert.equal(response.body.status, 'ready');
  assert.equal(response.body.documentation, '/api/health');
});

test('GET /api/health returns service health summary', async () => {
  const response = await request(app).get('/api/health');

  assert.equal(response.status, 200);
  assert.equal(response.body.success, true);
  assert.equal(response.body.service, 'verifica-ritorno-scuola');
  assert.equal(response.body.status, 'ok');
  assert.equal(typeof response.body.uptimeSeconds, 'number');
  assert.ok(response.body.database);
});

test('GET /api/does-not-exist returns a structured 404 payload', async () => {
  const response = await request(app).get('/api/does-not-exist');

  assert.equal(response.status, 404);
  assert.equal(response.body.success, false);
  assert.equal(response.body.error.code, 'NOT_FOUND');
  assert.match(response.body.error.message, /Route not found:/);
});

test('GET /api/error-demo returns a structured application error', async () => {
  const response = await request(app).get('/api/error-demo');

  assert.equal(response.status, 400);
  assert.equal(response.body.success, false);
  assert.equal(response.body.error.code, 'BAD_REQUEST');
  assert.equal(response.body.error.message, 'This is an intentionally generated client error.');
});
