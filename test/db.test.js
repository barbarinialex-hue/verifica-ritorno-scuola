import { initializeDatabase } from './db.js';

async function main() {
  try {
    const result = await initializeDatabase();
    console.log(result.message);
    process.exitCode = 0;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown database initialization error.';
    console.error(`Database initialization failed: ${message}`);
    process.exitCode = 1;
  }
}

main();
