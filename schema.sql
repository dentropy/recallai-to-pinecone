CREATE EXTENSION vector;

CREATE TABLE IF NOT EXISTS transcribed_snippits_t (
    id VARCHAR NOT NULL UNIQUE,
    chunk_test VARCHAR,
    speaker VARCHAR,
    from_timestamp VARCHAR,
    to_timestamp VARCHAR,
    from_timestamp_relative FLOAT,
    to_timestamp_relative FLOAT,
    transcript_id VARCHAR,
    record_id VARCHAR,
    bot_id VARCHAR
);

CREATE TABLE IF NOT EXISTS embedded_chats_t (
    id SERIAL PRIMARY KEY,
    transcript_id VARCHAR,
    model_name VARCHAR,
    from_timestamp_relative FLOAT,
    to_timestamp_relative FLOAT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    embedding VECTOR(768)
);
