import express from 'express';
import config from './config.js';
import { AppError, errorHandler, notFoundHandler } from './errors.js';

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
  const databaseState = config.databaseUrl
    ? {
        status: 'configured',
        message: 'Database connection string is present.',
      }
    : {
        status: 'not_configured',
        message: 'Set DATABASE_URL to enable database-level checks.',
      };

  res.status(200).json({
    success: true,
    service: 'verifica-ritorno-scuola',
    status: 'ok',
    environment: config.environment,
    uptimeSeconds: process.uptime(),
    database: databaseState,
  });
});

app.get('/api/error-demo', (req, res, next) => {
  next(new AppError(400, 'BAD_REQUEST', 'This is an intentionally generated client error.'));
});

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
