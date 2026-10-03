#!/bin/sh
# Runs once, on first boot of an empty Postgres volume. Keycloak keeps its own database
# on the shared server so a single volume holds all relational state.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
  CREATE DATABASE keycloak;
SQL
