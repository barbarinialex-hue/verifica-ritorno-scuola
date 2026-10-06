import dotenv from 'dotenv';

dotenv.config();

const rawPort = Number(process.env.PORT ?? 3000);

if (!Number.isInteger(rawPort) || rawPort <= 0) {
  throw new Error('PORT must be a valid integer greater than 0.');
}

const config = {
  appName: process.env.APP_NAME ?? 'Verifica Ritorno Scuola',
  environment: process.env.NODE_ENV ?? 'development',
  port: rawPort,
  databaseUrl: process.env.DATABASE_URL ?? '',
};

export default config;
