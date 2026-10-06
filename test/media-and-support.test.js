import fs from 'node:fs/promises';
import express from 'express';
import multer from 'multer';
import jwt from 'jsonwebtoken';

import config from './config.js';
import { getUserById, loginUser, registerUser, verifyToken } from './auth.js';
import { AppError, errorHandler, notFoundHandler } from './errors.js';
import { getDatabaseHealth, initializeDatabase } from './db.js';
import {
  createSegnalazione,
  deleteSegnalazione,
  getSegnalazioneById,
  listSegnalazioni,
  updateSegnalazione,
} from './segnalazioni.js';
import { createAttachment, listAttachmentsForSegnalazione } from './uploads.js';
import { addSupport, getSupportSummary, removeSupport } from './sostegni.js';

const app = express();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: config.maxUploadSizeBytes,
  },
  fileFilter: (req, file, callback) => {
    const mimeType = file.mimetype || '';
    const allowedMime = new Set([
      'image/jpeg',
      'image/png',
      'image/webp',
      'video/mp4',
      'video/quicktime',
      'video/webm',
    ]);

    if (allowedMime.has(mimeType)) {
      callback(null, true);
      return;
    }

    callback(new AppError(400, 'INVALID_FILE_TYPE', 'Tipo file non supportato. Inserire una foto o un video.'));
  },
});

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

await fs.mkdir(config.uploadDir, { recursive: true });

app.disable('x-powered-by');
app.use(express.json({ limit: '10mb' }));
app.use('/uploads', express.static(config.uploadDir));

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

app.get('/api/segnalazioni', async (req, res, next) => {
  try {
    const segnalazioni = await listSegnalazioni({
      categoriaId: req.query.categoriaId,
      quartiereId: req.query.quartiereId,
      stato: req.query.stato,
      limit: req.query.limit,
    });

    return res.status(200).json({
      success: true,
      data: segnalazioni,
      count: segnalazioni.length,
    });
  } catch (error) {
    return next(error);
  }
});

app.get('/api/segnalazioni/mie', authenticateRequest, async (req, res, next) => {
  try {
    const segnalazioni = await listSegnalazioni({ utenteId: req.user.id });

    return res.status(200).json({
      success: true,
      data: segnalazioni,
      count: segnalazioni.length,
    });
  } catch (error) {
    return next(error);
  }
});

app.get('/api/segnalazioni/:id', async (req, res, next) => {
  try {
    const segnalazione = await getSegnalazioneById(req.params.id);

    return res.status(200).json({
      success: true,
      data: segnalazione,
    });
  } catch (error) {
    return next(error);
  }
});

app.post('/api/segnalazioni', authenticateRequest, async (req, res, next) => {
  try {
    const segnalazione = await createSegnalazione(req.body, req.user);

    return res.status(201).json({
      success: true,
      data: segnalazione,
    });
  } catch (error) {
    return next(error);
  }
});

app.patch('/api/segnalazioni/:id', authenticateRequest, async (req, res, next) => {
  try {
    const segnalazione = await updateSegnalazione(req.params.id, req.body, req.user);

    return res.status(200).json({
      success: true,
      data: segnalazione,
    });
  } catch (error) {
    return next(error);
  }
});

app.delete('/api/segnalazioni/:id', authenticateRequest, async (req, res, next) => {
  try {
    const deleted = await deleteSegnalazione(req.params.id, req.user);

    return res.status(200).json({
      success: true,
      data: deleted,
    });
  } catch (error) {
    return next(error);
  }
});

app.get('/api/segnalazioni/:id/allegati', async (req, res, next) => {
  try {
    const allegati = await listAttachmentsForSegnalazione(req.params.id);
    return res.status(200).json({
      success: true,
      data: allegati,
      count: allegati.length,
    });
  } catch (error) {
    return next(error);
  }
});

app.post('/api/segnalazioni/:id/allegati', authenticateRequest, upload.single('file'), async (req, res, next) => {
  try {
    const allegato = await createAttachment({
      segnalazioneId: req.params.id,
      file: req.file,
      user: req.user,
    });

    return res.status(201).json({
      success: true,
      data: allegato,
    });
  } catch (error) {
    return next(error);
  }
});

app.get('/api/segnalazioni/:id/sostegno', async (req, res, next) => {
  try {
    const summary = await getSupportSummary(req.params.id, req.user ? req.user.id : null);
    return res.status(200).json({
      success: true,
      data: summary,
    });
  } catch (error) {
    return next(error);
  }
});

app.post('/api/segnalazioni/:id/sostegno', authenticateRequest, async (req, res, next) => {
  try {
    const summary = await addSupport({
      segnalazioneId: req.params.id,
      userId: req.user.id,
    });

    return res.status(201).json({
      success: true,
      data: summary,
    });
  } catch (error) {
    return next(error);
  }
});

app.delete('/api/segnalazioni/:id/sostegno', authenticateRequest, async (req, res, next) => {
  try {
    const summary = await removeSupport({
      segnalazioneId: req.params.id,
      userId: req.user.id,
    });

    return res.status(200).json({
      success: true,
      data: summary,
    });
  } catch (error) {
    return next(error);
  }
});

app.get('/api/error-demo', (req, res, next) => {
  next(new AppError(400, 'BAD_REQUEST', 'This is an intentionally generated client error.'));
});

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
