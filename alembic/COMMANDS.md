# Alembic Common Commands

## Database Migrations

### Apply Migrations
```bash
# Apply all pending migrations to latest
alembic upgrade head

# Apply specific number of migrations forward
alembic upgrade +2

# Apply to specific revision
alembic upgrade <revision_id>
```

### Create New Migrations
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration file
alembic revision -m "Description of changes"
```

### Migration History
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show verbose history with details
alembic history --verbose
```

### Rollback Migrations
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Migration Information
```bash
# Show pending migrations
alembic show <revision_id>

# Show SQL that would be executed (dry run)
alembic upgrade head --sql

# Show SQL for specific revision
alembic upgrade <revision_id> --sql
```

### Useful Flags
- `--verbose` - Show detailed output
- `--sql` - Show SQL without executing
- `--tag` - Add tag to revision

## Example Workflow

1. **Make model changes** in `src/app/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "Add model_id to experiment"`
3. **Review migration** file in `alembic/versions/`
4. **Apply migration**: `alembic upgrade head`
5. **Verify**: `alembic current`