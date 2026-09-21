import fs from 'node:fs/promises';
import {Pool} from 'pg';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) throw new Error('DATABASE_URL is required');

const pool = new Pool({connectionString});
const sql = await fs.readFile(new URL('../schema.sql', import.meta.url), 'utf8');

try {
  await pool.query(sql);
  console.log('metrics schema ready');
} finally {
  await pool.end();
}
