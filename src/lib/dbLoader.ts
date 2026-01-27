import initSqlJs from "sql.js";

const dbCache = new Map();

async function loadDB(path) {
  const SQL = await initSqlJs({
    locateFile: (file) => `/sql-wasm.wasm`
  });
  const res = await fetch(path);
  if (!res.ok) return null;
  const buf = await res.arrayBuffer();
  return new SQL.Database(new Uint8Array(buf));
}

export async function getDB(dataset, type) {
  const key = `${dataset}_${type}`;
  if (!dbCache.has(key)) {
    dbCache.set(
      key,
      loadDB(`/db/${dataset}_${type}.db`)
    );
  }
  return dbCache.get(key);
}