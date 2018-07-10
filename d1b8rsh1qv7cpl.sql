-- Adminer 4.6.3-dev PostgreSQL dump

\connect "d1b8rsh1qv7cpl";

DROP TABLE IF EXISTS "comments";
DROP SEQUENCE IF EXISTS comments_id_seq;
CREATE SEQUENCE comments_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

CREATE TABLE "public"."comments" (
    "id" integer DEFAULT nextval('comments_id_seq') NOT NULL,
    "zipcode" integer,
    "user_id" integer,
    "comment" character varying NOT NULL,
    CONSTRAINT "comments_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "comments_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) NOT DEFERRABLE,
    CONSTRAINT "comments_zipcode_fkey" FOREIGN KEY (zipcode) REFERENCES places(zipcode) NOT DEFERRABLE
) WITH (oids = false);


DROP TABLE IF EXISTS "places";
CREATE TABLE "public"."places" (
    "zipcode" integer NOT NULL,
    "city" text NOT NULL,
    "state" character varying NOT NULL,
    "lat" real NOT NULL,
    "long" real NOT NULL,
    "population" integer NOT NULL,
    CONSTRAINT "places_pkey" PRIMARY KEY ("zipcode")
) WITH (oids = false);


DROP TABLE IF EXISTS "users";
DROP SEQUENCE IF EXISTS users_user_id_seq;
CREATE SEQUENCE users_user_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

CREATE TABLE "public"."users" (
    "user_id" integer DEFAULT nextval('users_user_id_seq') NOT NULL,
    "username" character varying NOT NULL,
    "password" character varying NOT NULL,
    CONSTRAINT "user_name" UNIQUE ("username"),
    CONSTRAINT "users_pkey" PRIMARY KEY ("user_id")
) WITH (oids = false);


-- 2018-07-10 14:17:15.928638+00
