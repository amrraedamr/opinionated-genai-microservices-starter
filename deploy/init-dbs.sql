-- One logical database per service. Separate databases, not schemas: schemas
-- in a single database invite cross-service joins that the tooling allows.
CREATE DATABASE chat_api_db;
CREATE DATABASE identity_db;
