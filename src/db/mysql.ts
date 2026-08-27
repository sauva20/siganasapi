import mysql from 'mysql2/promise';

const connectionString = process.env.DATABASE_URL || "mysql://root:@localhost:3306/db_nanas_grading";
// Remove prisma connection limit query param if exists
const cleanUrl = connectionString.split('?')[0];

export const pool = mysql.createPool({
  uri: cleanUrl,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});
