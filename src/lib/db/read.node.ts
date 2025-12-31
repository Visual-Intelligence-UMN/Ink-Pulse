import Database from "better-sqlite3";
import path from "path";

export async function readSegmentResultsNode(dataset: string) {
  const dbPath = path.join(
    process.cwd(),
    "db",
    `${dataset}_segment_results.db`
  );

  const db = new Database(dbPath, { readonly: true });

  const rows = db
    .prepare("SELECT id, content FROM data")
    .all();

  db.close();

  return rows.map((r) => ({
    sessionId: r.id.replace(/\.json$/, ""),
    data: JSON.parse(r.content),
  }));
}