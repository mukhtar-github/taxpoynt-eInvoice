# TaxPoynt eInvoice Migration Strategy

## Migration Best Practices

To prevent recurring issues with multiple Alembic migration heads, follow these guidelines:

### Creating New Migrations

1. **Always start from the latest revision:**
   ```bash
   # Update your local database to the latest migration
   alembic upgrade head
   
   # Create a new migration
   alembic revision -m "descriptive_name_of_changes"
   ```

2. **Check for multiple heads before creating migrations:**
   ```bash
   # This should show only one head or a clear indication of which head to use
   alembic heads
   ```

3. **If multiple heads exist, merge them before creating new migrations:**
   ```bash
   alembic merge heads -m "merge_migration_description"
   alembic upgrade head
   ```

### Deployment Workflow

1. Always run `alembic heads` before deploying to ensure there's only one head
2. If multiple heads exist, create a merge migration locally, test it, and then deploy

### Environment-Specific Migrations

**Do not create separate branches for different environments (SQLite vs PostgreSQL)**.

Instead:
1. Use conditional logic within migrations based on dialect
2. Write migrations that work for both environments when possible

Example of dialect-aware migration:

```python
def upgrade():
    # Get the dialect
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = inspector.dialect.name
    
    # Apply changes conditionally based on dialect
    if dialect == 'sqlite':
        # SQLite-specific changes
        with op.batch_alter_table("table_name") as batch_op:
            batch_op.add_column(sa.Column('new_column', sa.String(), nullable=True))
    else:
        # PostgreSQL changes
        op.add_column('table_name', sa.Column('new_column', sa.String(), nullable=True))
```

### Testing Migrations

1. Test migrations on both SQLite and PostgreSQL before pushing
2. Use a CI pipeline to validate migrations on both database types

## Migration Structure

Maintain a single linear migration history by ensuring all new migrations depend on the latest head:

```
Base
  ↓
001_initial
  ↓
002_feature_x
  ↓
003_feature_y
```

## Handling Existing Multiple Heads

When you have multiple heads:

1. **Identify the heads:**
   ```bash
   alembic heads --verbose
   ```

2. **Create a merge migration:**
   ```bash
   alembic merge heads -m "merge_descriptive_name"
   ```

3. **Apply the merge:**
   ```bash
   alembic upgrade head
   ```

4. **Communicate with the team** that a merge has been performed

## Railway Deployment Considerations

For Railway, we maintain a start-up script that handles potential migration issues, but we should focus on preventing them by following these practices.
