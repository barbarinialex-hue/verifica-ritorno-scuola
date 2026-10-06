import express from 'express';
import config from './config.js';
import { AppError, errorHandler, notFoundHandler } from './errors.js';
import { getDatabaseHealth, initializeDatabase } from './db.js';

const app = express();

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

app.get('/api/error-demo', (req, res, next) => {
  next(new AppError(400, 'BAD_REQUEST', 'This is an intentionally generated client error.'));
});

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
