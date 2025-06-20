import { defineConfig } from "drizzle-kit";

const database =
  Bun.env.NODE_ENV === "production"
    ? Bun.env.PGDATABASE!
    : Bun.env.PGDATABASE_DEV!;

export default defineConfig({
  out: "./drizzle",
  schema: "./drizzle/schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    database,
    user: Bun.env.DATABASE_USER!,
    password: Bun.env.DATABASE_PASSWORD!,
    host: Bun.env.DATABASE_HOST!,
    port: parseInt(Bun.env.DATABASE_PORT!),
    ssl: {
      ca: Bun.env.DATABASE_SSL_CA,
    },
  },
});
