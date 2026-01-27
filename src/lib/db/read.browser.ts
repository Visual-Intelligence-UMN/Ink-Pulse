import { base } from '$app/paths';
import initSqlJs from 'sql.js';

const dbCache = new Map<string, any>();

export async function readSegmentResultsBrowser(dataset: string) {
  if (dbCache.has(dataset)) return dbCache.get(dataset);

  const SQL = await initSqlJs({
    locateFile: (file) => `${base}/sql-wasm/${file}`,
  });
  const isLocalBrowser =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const dbPath = isLocalBrowser
    ? `/db/${dataset}_segment_results.db`
    : `${base}/db/${dataset}_segment_results.db`;

  const res = await fetch(dbPath);
  if (!res.ok) {
    console.warn("DB not found, fallback needed");
    return [];
  }
  const buf = await res.arrayBuffer();
  const db = new SQL.Database(new Uint8Array(buf));
  const result = db.exec("SELECT id, content FROM data");
  if (!result.length) return [];
  const { columns, values } = result[0];
  const idIdx = columns.indexOf("id");
  const contentIdx = columns.indexOf("content");

  const data = values.map((row) => ({
    id: row[idIdx].replace(/\.json$/, ""),
    content: JSON.parse(row[contentIdx]),
  }));

  dbCache.set(dataset, data);
  return data;
}
