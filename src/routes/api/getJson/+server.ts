import { json } from "@sveltejs/kit";
import { connectDB } from "$lib/db";
import { jsonTable } from "$lib/db/schema";
import { eq } from "drizzle-orm";

export async function GET({ url }) {
  const group = url.searchParams.get("group") || "creative";
  const db = connectDB();
  const jsonData = db
    .select()
    .from(jsonTable)
    .where(eq(jsonTable.group, group))
    .all();

  return json({ jsonData });
}
