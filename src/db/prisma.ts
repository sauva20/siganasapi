import { PrismaClient } from "@prisma/client";

import { PrismaClient as PC } from "@prisma/client";
import { PrismaMysql } from "@prisma/adapter-mysql2";
import mysql from "mysql2/promise";

declare global {
  var prisma: PC | undefined;
}

// Initialize the database connection pool using mysql2
const connectionString = process.env.DATABASE_URL || "mysql://root:@localhost:3306/db_nanas_grading";
const pool = mysql.createPool(connectionString);

// Initialize the Prisma adapter
const adapter = new PrismaMysql(pool);

// Pass the adapter to PrismaClient
export const prisma =
  global.prisma ||
  new PC({
    adapter,
    log: ["query", "info", "warn", "error"],
  });

if (process.env.NODE_ENV !== "production") global.prisma = prisma;
