import { pgTable, uuid, vector } from "drizzle-orm/pg-core";

export const embeddings = pgTable("embeddings", {
  id: uuid("id").primaryKey().defaultRandom(),
  postId: uuid("post_id").notNull(),
  embeddings: vector("embeddings", {
    dimensions: 1024,
  }),
});
