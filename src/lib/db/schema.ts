import { sqliteTable, text, primaryKey } from "drizzle-orm/sqlite-core";

export const jsonTable = sqliteTable(
  "json_table",
  {
    id: text("id").notNull(),
    group: text("group").notNull(),
    content: text("content").notNull()
  },
  (table) => ({
    pk: primaryKey(table.id, table.group)
  })
);

export const segmentTable = sqliteTable(
  "segment_table",
  {
    id: text("id").notNull(),
    group: text("group").notNull(),
    content: text("content").notNull()
  },
  (table) => ({
    pk: primaryKey(table.id, table.group)
  })
);
