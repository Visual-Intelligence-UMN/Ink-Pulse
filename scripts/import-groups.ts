import fs from "fs";
import path from "path";
import { connectDB } from "../src/lib/db/index.js";
import { jsonTable, segmentTable } from "../src/lib/db/schema.js";

const datasetNames: string[] = JSON.parse(
  fs.readFileSync(path.join("static", "dataset_name.json"), "utf8")
);

function importGroup(group: string) {
  const db = connectDB();
  const base = path.join("static", "dataset", group);
  const jsonFolder = path.join(base, "json");
  if (fs.existsSync(jsonFolder)) {
    for (const file of fs.readdirSync(jsonFolder)) {
      const filePath = path.join(jsonFolder, file);
      const raw = fs.readFileSync(filePath, "utf8");
      const itemToInsert = {
        id: file,
        group,
        content: raw
      };
    }
  }

  const segmentFolder = path.join(base, "segment_results");
  if (fs.existsSync(segmentFolder)) {
    for (const file of fs.readdirSync(segmentFolder)) {
      const filePath = path.join(segmentFolder, file);
      const raw = fs.readFileSync(filePath, "utf8");
      const itemToInsert = {
        id: file,
        group,
        content: raw
      };
    }
  }
}

(async () => {
  for (const group of datasetNames) {
    importGroup(group);
  }
  console.log("All groups imported.");
})();