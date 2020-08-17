BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "games" (
	"id"	INTEGER NOT NULL UNIQUE,
	"score"	INTEGER,
	"user_id"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"login"	TEXT,
	"wallet"	INTEGER,
	"name"	text,
	CONSTRAINT "users_pk" PRIMARY KEY("id")
);
CREATE UNIQUE INDEX IF NOT EXISTS "users_id_uindex" ON "users" (
	"id"
);
COMMIT;
