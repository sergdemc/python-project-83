DROP TABLE if exists urls CASCADE;
DROP TABLE if exists url_checks CASCADE;

CREATE TABLE urls (
id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
name VARCHAR(255) UNIQUE NOT NULL,
created_at DATE
);

CREATE TABLE url_checks (
id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
url_id bigint REFERENCES urls(id) ON DELETE CASCADE,
status_code bigint,
h1 VARCHAR(255),
title VARCHAR(255),
description VARCHAR(255),
created_at DATE
);