import fs from "fs";
import path from "path";
import { connectDB } from "../src/lib/db/index.js";
import { jsonTable, segmentTable } from "../src/lib/db/schema.js";
import { ensureSchema } from "./ensureSchema.js";

const datasetNames: string[] = JSON.parse(
  fs.readFileSync(path.join("static", "dataset_name.json"), "utf8")
);

function importFolder(dbName: string, folder: string, table: any, isComplex = false) {
  const { db, dbFile } = connectDB(dbName);
  ensureSchema(dbFile, isComplex);

  if (!fs.existsSync(folder)) return;

  for (const file of fs.readdirSync(folder)) {
    const raw = fs.readFileSync(path.join(folder, file), "utf8");
    const sessionId = file.replace(/\.json$/, "");
    if (isComplex) {
      const parsed = JSON.parse(raw);
      const actions = parsed.actions ?? [];
      db.insert(table).values({
        id: sessionId,
        initText: parsed.init_text ?? null,
        textLength: parsed.text ?? null,
        initTime: parsed.init_time ?? null,
        endTime: parsed.end_time ?? null,
        actions: JSON.stringify(actions),
      }).run();
    } else {
      db.insert(table).values({
        id: sessionId,
        content: raw,
      }).run();
    }
  }
}

(async () => {
  for (const group of datasetNames) {
    console.log(`Importing ${group}...`);
    const base = path.join("static", "dataset", group);
    importFolder(`${group}_json`, path.join(base, "json"), jsonTable, true);
    importFolder(`${group}_segment_results`, path.join(base, "segment_results"), segmentTable, false);
  }
  console.log("All groups imported.");
})();
