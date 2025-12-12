import { json } from "@sveltejs/kit";
import { connectDB } from "$lib/db";
import { jsonTable, segmentTable } from "$lib/db/schema";
import fs from "fs";
import path from "path";
import { eq } from "drizzle-orm";

const datasetNames: string[] = JSON.parse(
  fs.readFileSync(path.join("static", "dataset_name.json"), "utf8")
);

export async function GET({ url }) {
  const group = url.searchParams.get("group") || datasetNames[0];
  if (!datasetNames.includes(group)) {
    return json({ error: "Unknown Dataset" }, { status: 400 });
  }

  const db = connectDB();
  const jsonData = db
    .select()
    .from(jsonTable)
    .where(eq(jsonTable.group, group))
    .all();
  const segmentData = db
    .select()
    .from(segmentTable)
    .where(eq(segmentTable.group, group))
    .all();

  return json({ jsonData, segmentData });
}