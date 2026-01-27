import { json } from "@sveltejs/kit";
import { connectDB } from "$lib/db";
import { jsonTable } from "$lib/db/schema";

export async function GET({ url }) {
  const dataset = url.searchParams.get("dataset") ?? "creative";
  const { db } = connectDB(`${dataset}_json`);
  const jsonData = db.select().from(jsonTable).all();

  return json({
    exists: jsonData.length > 0,
    jsonData,
  });
}
