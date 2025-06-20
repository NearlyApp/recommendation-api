import { drizzle } from "drizzle-orm/postgres-js";
import postgres, { type Sql } from "postgres";
import * as schema from "./schema";

const URI = `${Bun.env.PGURI}/${
  Bun.env.NODE_ENV === "production"
    ? Bun.env.PGDATABASE!
    : Bun.env.PGDATABASE_DEV!
}`;

let connection: Sql<{}>;

if (Bun.env.NODE_ENV === "production") {
  connection = postgres(URI, {
    prepare: false,
  });
  console.log("PG ML connected.");
} else {
  const globalConnection = global as typeof globalThis & {
    connection: Sql<{}>;
  };

  if (!globalConnection.connection) {
    globalConnection.connection = postgres(URI, {
      prepare: false,
    });
    console.log("PG ML connected.");
  }

  connection = globalConnection.connection;
}

const db = drizzle(connection, {
  schema,
  logger: true,
});

export default db;
