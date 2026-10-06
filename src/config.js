import path from 'node:path';
import dotenv from 'dotenv';

dotenv.config();

const rawPort = Number(process.env.PORT ?? 3000);

if (!Number.isInteger(rawPort) || rawPort <= 0) {
  throw new Error('PORT must be a valid integer greater than 0.');
}

const uploadDir = path.resolve(process.cwd(), process.env.UPLOAD_DIR ?? 'uploads');
const rawMaxSizeMb = Number(process.env.MAX_UPLOAD_SIZE_MB ?? 5);
if (!Number.isFinite(rawMaxSizeMb) || rawMaxSizeMb <= 0) {
  throw new Error('MAX_UPLOAD_SIZE_MB must be a positive number.');
}

const config = {
  appName: process.env.APP_NAME ?? 'Verifica Ritorno Scuola',
  environment: process.env.NODE_ENV ?? 'development',
  port: rawPort,
  databaseUrl: process.env.DATABASE_URL ?? '',
  jwtSecret: process.env.JWT_SECRET ?? 'dev-secret-change-me',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN ?? '7d',
  uploadDir,
  maxUploadSizeBytes: Math.round(rawMaxSizeMb * 1024 * 1024),
};

export default config;
