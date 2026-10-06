import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

import { AppError } from './errors.js';

const { Pool } = pg;
const schemaPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'db', 'schema.sql');

export function createPool() {
  const connectionString = process.env.DATABASE_URL;

  if (!connectionString) {
    return null;
  }

  return new Pool({
    connectionString,
    max: 10,
    idleTimeoutMillis: 30_000,
    statement_timeout: 5_000,
  });
}

export const pool = createPool();

export async function getDatabaseHealth() {
  if (!pool) {
    return {
      status: 'not_configured',
      message: 'DATABASE_URL is not set. Database schema is not initialized yet.',
    };
  }

  try {
    const result = await pool.query('SELECT NOW() AS now, current_database() AS database_name;');

    return {
      status: 'ok',
      message: 'Database connection successful.',
      now: result.rows[0].now,
      databaseName: result.rows[0].database_name,
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Database connection failed.',
    };
  }
}

export async function initializeDatabase() {
  if (!pool) {
    throw new AppError(
      500,
      'DB_NOT_CONFIGURED',
      'DATABASE_URL is not configured. Set it before initializing the schema.'
    );
  }

  const schemaSql = fs.readFileSync(schemaPath, 'utf8');

  try {
    await pool.query(schemaSql);

    return {
      status: 'ok',
      message: 'Database schema initialized successfully.',
    };
  } catch (error) {
    throw new AppError(
      500,
      'DB_INIT_FAILED',
      error instanceof Error ? error.message : 'Database schema could not be initialized.',
      {
        detail: 'Check the connection string and the SQL migration file.',
      }
    );
  }
}
