# Test Database Setup

This project uses Docker to create a local PostgreSQL database for testing. The database is initialized with the required tables, test data is added with SQL queries, and the results are printed so the setup can be checked.

## Prerequisites

Install or enable the following before running the setup:

- Docker Desktop
- WSL (Windows Subsystem for Linux)
- A WSL distribution, such as Ubuntu

Docker must also be enabled for your WSL distribution:

1. Open Docker Desktop.
2. Go to **Settings > Resources > WSL Integration**.
3. Enable integration for the WSL distribution you use.
4. Select **Apply & Restart** if Docker Desktop asks you to.

You can verify that Docker is available in WSL with:

```bash
docker --version
docker compose version
```

## Automated Setup

From the project root, run the shell script in WSL:

```bash
cd /mnt/c/Users/<username>/OneDrive/Desktop/Git/CropCapture
bash TEST_DB_SETUP.sh
```

The `TEST_DB_SETUP.sh` script packs the complete setup process into one command. It:

1. Starts or recreates the PostgreSQL Docker service using `db_testing/docker-compose.yml`.
2. Waits for PostgreSQL to become ready.
3. Resets the existing `testDB` table, if one exists.
4. Runs `db_testing/initializeDB.sql` to create the test database table structure.
5. Runs `db_testing/testDBQuery.sql` to insert and query test data.
6. Runs `db_testing/DBInfoPrint.sql` to print the database contents.

The Docker Compose configuration uses the PostgreSQL 15 image and creates a database with these test credentials:

```text
Database: testing_db
User: myuser
Password: testing_password
Port: 5432
```

The database data is stored in a Docker volume named `pgdata`, so it can survive container restarts.

## Manual SQL Files

The SQL files are stored in the `db_testing` directory:

- `initializeDB.sql` creates the tables and database structure needed for testing.
- `testDBQuery.sql` adds sample test data and runs test queries.
- `DBInfoPrint.sql` displays the current database contents.

Normally, you do not need to run these files manually because `TEST_DB_SETUP.sh` runs them in the correct order.

## Troubleshooting

If WSL reports errors such as `$'\r': command not found`, the shell script has Windows line endings. Convert it to Unix line endings with:

```bash
sed -i 's/\r$//' TEST_DB_SETUP.sh
```

Then run the setup script again.
