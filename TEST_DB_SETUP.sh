#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DB_TESTING_DIR="$SCRIPT_DIR/db_testing"
COMPOSE_FILE="$DB_TESTING_DIR/docker-compose.yml"
DB_USER="myuser"
DB_NAME="testing_db"

if ! command -v docker >/dev/null 2>&1; then
	echo "Docker is not available in this WSL distribution." >&2
	echo "Enable Docker Desktop WSL Integration for this distribution, then rerun this script." >&2
	exit 1
fi

compose() {
	docker compose --file "$COMPOSE_FILE" "$@"
}

echo "Creating or recreating the PostgreSQL service..."
compose up --detach --force-recreate db

echo "Waiting for PostgreSQL to be ready..."
for attempt in {1..30}; do
	if compose exec --no-TTY db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
		break
	fi

	if [[ "$attempt" -eq 30 ]]; then
		echo "PostgreSQL did not become ready in time." >&2
		exit 1
	fi

	sleep 1
done

psql() {
	compose exec --no-TTY db psql \
		-v ON_ERROR_STOP=1 \
		-U "$DB_USER" \
		-d "$DB_NAME" \
		"$@"
}

echo "Resetting the test table..."
psql -c 'DROP TABLE IF EXISTS testDB;'

echo "Initializing the database..."
psql < "$DB_TESTING_DIR/initializeDB.sql"

echo "Running test queries..."
psql < "$DB_TESTING_DIR/testDBQuery.sql"

echo "Printing database contents..."
psql < "$DB_TESTING_DIR/DBInfoPrint.sql"

echo "Database setup and verification completed."