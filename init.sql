CREATE DATABASE IF NOT EXISTS db;

CREATE TABLE IF NOT EXISTS db.raw_table
(
    data String,
    _inserted_at DateTime
)
ENGINE = MergeTree()
ORDER BY _inserted_at;

INSERT INTO db.raw_table SELECT *
FROM s3('http://api.open-notify.org/astros.json')


CREATE MATERIALIZED VIEW IF NOT EXISTS db.raw_to_parsed_mv 
TO db.parsed_table 
AS
SELECT 
    JSONExtractString(data, 'craft') AS craft,
    JSONExtractString(data, 'name') AS name,
    _inserted_at
FROM db.raw_table;

CREATE TABLE IF NOT EXISTS db.parsed_table
(
    craft String,
    name String,
    _inserted_at DateTime
)
ENGINE = MergeTree()
ORDER BY _inserted_at;

SELECT * FROM parsed_table;