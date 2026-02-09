import fs from "fs";
import path from "path";
import Database from "better-sqlite3";
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const jsonTable = sqliteTable("data", {
  id: text("id").primaryKey(),
  initText: text("init_text"),
  textLength: integer("text_length"),
  initTime: text("init_time"),
  endTime: text("end_time"),
  actions: text("actions"),
  bars: text("bars"),
});

export const segmentTable = sqliteTable("data", {
  id: text("id").primaryKey(),
  content: text("content"),
});

function ensureSchema(dbFile: string, tableType: "json" | "segment") {
  const db = new Database(dbFile);
  if (tableType === "json") {
    const tableInfo = db.prepare(`PRAGMA table_info(data);`).all();
    const hasBars = tableInfo.some((col) => col.name === "bars");
    if (!tableInfo.length) {
      db.exec(`
        CREATE TABLE data (
          id TEXT PRIMARY KEY,
          init_text TEXT,
          text_length INTEGER,
          init_time TEXT,
          end_time TEXT,
          actions TEXT,
          bars TEXT
        );
      `);
    } else if (!hasBars) {
      db.exec(`ALTER TABLE data ADD COLUMN bars TEXT;`);
    }
  } else {
    const tableInfo = db.prepare(`PRAGMA table_info(data);`).all();
    if (!tableInfo.length) {
      db.exec(`
        CREATE TABLE data (
          id TEXT PRIMARY KEY,
          content TEXT
        );
      `);
    }
  }
  db.close();
}

function connectDB(dbName: string) {
  const dbFile = path.join(path.join(process.cwd(), "static", "db"), `${dbName}.db`);
  const db = new Database(dbFile);
  return { db, dbFile };
}

const scoreMap = new Map<string, number>();

function loadSessionScores(csvPath: string) {
  if (!fs.existsSync(csvPath)) return;
  const lines = fs.readFileSync(csvPath, "utf8").split("\n");
  lines.slice(1).forEach((line) => {
    if (!line.trim()) return;
    const [session_id, judge_score] = line.split(",");
    if (session_id) scoreMap.set(session_id, Number(judge_score));
  });
}

function actionsToPointsBackend(parsed: any) {
  const { actions, text: totalTextLength, init_text } = parsed;
  if (!actions || !actions.length) return [];

  let currentCharCount = init_text?.length ?? 0;
  const baseTime = new Date(actions[0].event_time).getTime() / 1000;

  return actions.map((a) => {
    const time = new Date(a.event_time).getTime() / 1000 - baseTime;

    if (a.name === "text-insert") currentCharCount += a.text?.length ?? 0;
    else if (a.name === "text-delete") currentCharCount -= a.text?.length ?? 0;

    const percentage = totalTextLength > 0 ? currentCharCount / totalTextLength : 0;

    return {
      time,
      percentage,
      eventSource: a.eventSource || "user",
      residual_vector_norm: 0,
    };
  });
}

function matchPointsWithSimilarity(points: any[], similarityData: any[]) {
  if (!similarityData || !similarityData.length) return points;
  return points
    .map((p) => {
      const matched = similarityData.find(
        (s) => s.start_progress <= p.percentage && s.end_progress >= p.percentage
      );
      if (!matched) return null;
      return { ...p, residual_vector_norm: matched.residual_vector_norm ?? 0 };
    })
    .filter(Boolean);
}

function handleLine2Bar(points: any[], sentenceValue: number, scoreValue: number | null) {
  if (!points || !points.length) return [];

  const bars: any[] = [];
  let currentBar = [points[0]];
  let lastSource = points[0].eventSource;
  let lastTrend = 0;
  let lastSemantic = points[0].residual_vector_norm ?? 0;
  for (let i = 1; i < points.length; i++) {
    const p = points[i];
    const prev = points[i - 1];
    const progress = p.percentage ?? 0;
    const prevProgress = prev.percentage ?? 0;
    let trend = lastTrend;
    if (progress > prevProgress) trend = 1;
    else if (progress < prevProgress) trend = -1;
    const sourceChanged = p.eventSource !== lastSource;
    const trendChanged = lastTrend !== 0 && trend !== lastTrend;
    const semanticChanged = (p.residual_vector_norm ?? 0) !== lastSemantic;

    if (sourceChanged || trendChanged || semanticChanged) {
      bars.push(currentBar);
      currentBar = [];
    }

    currentBar.push(p);
    lastSource = p.eventSource;
    lastTrend = trend;
    lastSemantic = p.residual_vector_norm ?? 0;
  }

  if (currentBar.length) bars.push(currentBar);

  return bars.map((bar) => {
    const first = bar[0];
    const last = bar[bar.length - 1];
    return {
      sentence: sentenceValue,
      source: first.eventSource,
      start_progress: first.percentage,
      end_progress: last.percentage,
      start_time: first.time,
      end_time: last.time,
      last_event_time: last.time,
      residual_vector_norm: last.residual_vector_norm ?? 0,
      score: scoreValue,
    };
  });
}

function importFolder(dbName: string, folder: string, table: any, isComplex = false) {
  const { db, dbFile } = connectDB(dbName);
  ensureSchema(dbFile, isComplex ? "json" : "segment");

  if (!fs.existsSync(folder)) return;

  for (const file of fs.readdirSync(folder)) {
    const raw = fs.readFileSync(path.join(folder, file), "utf8");
    const sessionId = file.replace(/\.json$/, "");

    if (isComplex) {
      const parsed = JSON.parse(raw);
      const actions = parsed.actions ?? [];
      const segmentDb = connectDB(`${dbName.replace("_json", "_segment_results")}`).db;
      let similarityData: any[] = [];
      try {
        const row = segmentDb.prepare("SELECT content FROM data WHERE id = ?").get(sessionId);
        similarityData = row ? JSON.parse(row.content) : [];
      } catch { }
      segmentDb.close();

      const points = actionsToPointsBackend(parsed);
      const enrichedPoints = matchPointsWithSimilarity(points, similarityData);

      const sentenceValue = (parsed.text ?? 0) / 3000;
      const scoreValue = scoreMap.get(sessionId) ?? null;
      const bars = handleLine2Bar(enrichedPoints, sentenceValue, scoreValue);

      db.prepare(`
        INSERT OR REPLACE INTO data
        (id, init_text, text_length, init_time, end_time, actions, bars)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `).run(
        sessionId,
        parsed.init_text ?? null,
        parsed.text ?? null,
        parsed.init_time ?? null,
        parsed.end_time ?? null,
        JSON.stringify(actions),
        JSON.stringify(bars)
      );

    } else {
      db.prepare(`
        INSERT OR REPLACE INTO data
        (id, content)
        VALUES (?, ?)
      `).run(sessionId, raw);
    }
  }

  db.close();
}

const datasetNames: string[] = JSON.parse(
  fs.readFileSync(path.join("static", "dataset_name.json"), "utf8")
);

loadSessionScores("session.csv");

for (const group of datasetNames) {
  console.log(`Processing group: ${group}...`);
  const base = path.join("static", "dataset", group);

  const jsonFolder = path.join(base, "json");
  const segmentFolder = path.join(base, "segment_results");

  importFolder(`${group}_segment_results`, segmentFolder, segmentTable, false);
  importFolder(`${group}_json`, jsonFolder, jsonTable, true);
}

console.log("All groups processed.");
