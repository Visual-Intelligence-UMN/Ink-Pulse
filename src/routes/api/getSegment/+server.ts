import { json } from "@sveltejs/kit";
import { connectDB } from "$lib/db";
import { segmentTable } from "$lib/db/schema";
import { eq } from "drizzle-orm";

export function GET({ url }) {
  const group = url.searchParams.get("group") || "creative";
  const db = connectDB();
  const segmentData = db
    .select()
    .from(segmentTable)
    .where(eq(segmentTable.group, group))
    .all();

  return json({ segmentData });
}