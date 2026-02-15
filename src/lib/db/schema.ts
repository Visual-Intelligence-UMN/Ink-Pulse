import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const jsonTable = sqliteTable("data", {
  id: text("id").primaryKey(),
  initText: text("init_text"),
  textLength: integer("text_length"),
  initTime: text("init_time"),
  endTime: text("end_time"),
  actions: text("actions"),
  content: text("content"),
});

export const segmentTable = sqliteTable("data", {
  id: text("id").primaryKey(),
  content: text("content"),
});
