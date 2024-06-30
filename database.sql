CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    created_at DATE
);

CREATE TABLE IF NOT EXISTS url_checks (
    id SERIAL PRIMARY KEY,
    url_id BIGINT REFERENCES urls(id),
    status_code INTEGER,
    h1 VARCHAR(255),
    description TEXT,
    created_at DATE
);