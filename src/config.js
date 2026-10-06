import express from 'express';
import jwt from 'jsonwebtoken';

import config from './config.js';
import { getUserById, loginUser, registerUser, verifyToken } from './auth.js';
import { AppError, errorHandler, notFoundHandler } from './errors.js';
import { getDatabaseHealth, initializeDatabase, pool } from './db.js';

const app = express();

async function authenticateRequest(req, res, next) {
  try {
    const header = req.headers.authorization ?? '';
    const token = header.startsWith('Bearer ') ? header.slice(7).trim() : null;

    if (!token) {
      throw new AppError(401, 'AUTH_REQUIRED', 'Authorization header mancante o non valido.');
    }

    const payload = verifyToken(token);
    const user = await getUserById(Number(payload.sub));

    if (!user) {
      throw new AppError(401, 'INVALID_TOKEN', 'Token non valido o utente non trovato.');
    }

    req.user = user;
    return next();
  } catch (error) {
    if (error instanceof jwt.JsonWebTokenError || error instanceof jwt.TokenExpiredError) {
      return next(new AppError(401, 'INVALID_TOKEN', 'Token non valido o scaduto.'));
    }

    return next(error);
  }
}

app.disable('x-powered-by');
app.use(express.json({ limit: '1mb' }));

app.get('/', (req, res) => {
  res.status(200).json({
    name: config.appName,
    status: 'ready',
    environment: config.environment,
    documentation: '/api/health',
    message: 'Foundation project scaffold for the civic reporting platform.',
  });
});

app.get('/api/health', async (req, res) => {
  const database = await getDatabaseHealth();

  const responseBody = {
    success: true,
    service: 'verifica-ritorno-scuola',
    status: database.status === 'error' ? 'degraded' : 'ok',
    environment: config.environment,
    uptimeSeconds: process.uptime(),
    database,
  };

  if (database.status === 'error') {
    return res.status(503).json(responseBody);
  }

  return res.status(200).json(responseBody);
});

app.post('/api/database/init', async (req, res, next) => {
  try {
    const result = await initializeDatabase();

    return res.status(201).json({
      success: true,
      ...result,
    });
  } catch (error) {
    return next(error);
  }
});

app.post('/api/auth/register', async (req, res, next) => {
  try {
    const payload = await registerUser({
      nome: req.body.nome,
      cognome: req.body.cognome,
      email: req.body.email,
      password: req.body.password,
      tipoRuolo: req.body.tipoRuolo,
      quartiereId: req.body.quartiereId ?? req.body.fkQuartiere,
    });

    return res.status(201).json({
      success: true,
      token: payload.token,
      user: payload.user,
    });
  } catch (error) {
    return next(error);
  }
});

app.post('/api/auth/login', async (req, res, next) => {
  try {
    const payload = await loginUser({
      email: req.body.email,
      password: req.body.password,
    });

    return res.status(200).json({
      success: true,
      token: payload.token,
      user: payload.user,
    });
  } catch (error) {
    return next(error);
  }
});

app.get('/api/auth/me', authenticateRequest, async (req, res) => {
  return res.status(200).json({
    success: true,
    user: req.user,
  });
});

app.get('/api/error-demo', (req, res, next) => {
  next(new AppError(400, 'BAD_REQUEST', 'This is an intentionally generated client error.'));
});

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
