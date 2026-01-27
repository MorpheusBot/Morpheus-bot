# Database-related guidelines

## Connecting to the DB through Docker (externally)

```bash
docker compose exec -it db psql -U morpheus
```

PostgreSQL prompt will open and you can now run any SQL (or Postgre-specific) commands you want. To quit, press Ctrl+D.

## Database Migrations (Alembic)

This project uses Alembic for database migrations. Migrations allow you to version control your database schema changes.

### Running Migrations

Before running migrations, make sure you have activated the virtual environment:

```bash
source venv/bin/activate
```

To upgrade your database to the latest version:

```bash
alembic upgrade head
```

To check the current migration version:

```bash
alembic current
```

To view migration history:

```bash
alembic history
```

### Creating New Migrations

When you make changes to database models, you need to create a new migration:

1. Make your changes to the SQLAlchemy models in `database/` directory
2. Auto-generate a migration file (Alembic will detect changes automatically):

```bash
alembic revision --autogenerate -m "description of your changes"
```

3. Review the generated migration file in `database/migrations/versions/` to ensure it captured all changes correctly
4. Apply the migration:

```bash
alembic upgrade head
```

> [!NOTE]
> The `--autogenerate` flag compares your SQLAlchemy models with the current database schema and automatically generates the upgrade/downgrade logic. Always review the generated migration before applying it.

### Stamping the Database

If you have an existing database that wasn't created with migrations, you need to stamp it with the current revision:

```bash
alembic stamp head
```

Or stamp with a specific revision:

```bash
alembic stamp <revision_id>
```

### Migration Notes

- The migration script automatically detects whether it's running inside or outside Docker
- When running outside Docker, it connects to the database using the container's IP address
- When running inside Docker, it uses the service name `postgres`
- Always test migrations in a development environment before applying to production

## Enable debug prints

Add `echo=True` to `database/__init__.py`:

```python
8   self.engine = create_async_engine(config.db_string, echo=False)
                                                        ^
```

## Database backup/restore

> [!Note]
> For most of these operations you need the database container running.
> ```bash
> docker compose up -d db
> ```

To backup the database, run the following command:

```bash
docker compose exec db pg_dump -U morpheus -d morpheus > backup.sql
```

Restore the database from the backup file automatically by running the following commands:

> [!Note]
> Backup.sql with data must be in `database/backup/backup.sql`

```bash
docker compose down
docker volume rm morpheus_postgres_data
docker compose up --build -d
```

To manually restore the database, run the following commands:

```bash
# drop and recreate the database must be separate commands
docker compose exec db psql -U morpheus -d postgres -c "DROP DATABASE morpheus;"
docker compose exec db psql -U morpheus -d postgres -c "CREATE DATABASE morpheus WITH OWNER morpheus;"

# restore the database from the backup file
docker compose exec -T db psql -U morpheus < backup.sql
```

You can drop specific table using this command:

```bash
docker compose exec db psql -U morpheus -c "DROP TABLE [table_name] CASCADE;"
```

To get only specific table and it's data use this command:

```bash
docker compose exec db pg_dump -U morpheus -d morpheus -t [table_name] > [table_name].sql
```
