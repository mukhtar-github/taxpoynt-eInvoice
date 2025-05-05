from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from several possible locations
# First trying .env.development, then falling back to .env
dotenv_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.development'),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
]

for dotenv_path in dotenv_paths:
    if os.path.exists(dotenv_path):
        print(f"Loaded environment variables from {dotenv_path}")
        load_dotenv(dotenv_path)
        break

# Import the SQLAlchemy declarative Base object
from app.db.base import Base
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Prioritize SQLite for development
database_url = os.getenv("DATABASE_URL")
url = database_url if database_url and "sqlite" in database_url and settings.APP_ENV == "development" else str(settings.SQLALCHEMY_DATABASE_URI)
config.set_main_option("sqlalchemy.url", url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if database_url and "sqlite" in database_url and settings.APP_ENV == "development":
            from sqlalchemy import JSON, TypeDecorator
            from sqlalchemy.ext.declarative import declarative_base
            from sqlalchemy.dialects.postgresql import JSONB
            
            class SQLiteJSONB(TypeDecorator):
                impl = JSON
                cache_ok = True

            # Replace PostgreSQL JSONB with SQLite compatible JSON for SQLite connections
            from sqlalchemy.dialects.postgresql import base as postgresql_base
            postgresql_base.ischema_names['jsonb'] = JSON
            
            # Handle JSONB columns in migrations
            def process_revision_directives(context, revision, directives):
                script = directives[0]
                if script.upgrade_ops:
                    # Replace JSONB with JSON in upgrade operations
                    for op in script.upgrade_ops.ops:
                        if hasattr(op, 'columns'):
                            for col in op.columns:
                                if hasattr(col, 'type') and isinstance(col.type, JSONB):
                                    col.type = JSON()
                return script

            # Register the directive processor
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                process_revision_directives=process_revision_directives,
                include_schemas=True
            )
        else:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_schemas=True
            )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
