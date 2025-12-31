import Database from "better-sqlite3";

export function ensureSchema(dbFile: string, isComplex = false) {
  const db = new Database(dbFile);
  if (isComplex) {
    db.exec(`
      CREATE TABLE IF NOT EXISTS data (
        id TEXT PRIMARY KEY,
        init_text TEXT,
        text_length INTEGER,
        init_time TEXT,
        end_time TEXT,
        actions TEXT
      );
    `);
  } else {
    db.exec(`
      CREATE TABLE IF NOT EXISTS data (
        id TEXT PRIMARY KEY,
        content TEXT
      );
    `);
  }
  db.close();
}
