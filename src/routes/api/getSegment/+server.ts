import { json } from "@sveltejs/kit";
import { connectDB } from "$lib/db";
import { segmentTable } from "$lib/db/schema";

export async function GET({ url }) {
  const dataset = url.searchParams.get("dataset") ?? "creative";
  const { db } = connectDB(`${dataset}_segment_results`);
  const segmentData = db.select().from(segmentTable).all();

  return json({
    exists: segmentData.length > 0,
    segmentData,
  });
}
