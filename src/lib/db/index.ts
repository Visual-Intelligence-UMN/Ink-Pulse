import fs from "fs";
import path from "path";
import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";
import * as schema from "./schema.js";

export function connectDB() {
  const dbDir = path.join(process.cwd(), "db");
  console.log("index dbDir", dbDir)
  if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });

  const dbFile = path.join(dbDir, "local.db");
  const sqlite = new Database(dbFile);
  return drizzle(sqlite, { schema });
}