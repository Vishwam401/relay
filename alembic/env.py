from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import our models so Alembic can detect schema changes.
# Base.metadata contains all table definitions from models.py.
from src.models import Base  # noqa: E402

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def configure_url() -> tuple[str, str]:
    import os
    from sqlalchemy.engine.url import make_url

    has_cli_c = bool(getattr(config, "cmd_opts", None) and getattr(config.cmd_opts, "config", None))
    is_custom_ini = bool(config.config_file_name and os.path.basename(config.config_file_name) != "alembic.ini")

    if has_cli_c or is_custom_ini:
        source = "-c"
    else:
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            sync_url = env_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
            config.set_main_option("sqlalchemy.url", sync_url)
            source = "env"
        else:
            source = "alembic.ini"

    raw_url = config.get_main_option("sqlalchemy.url")
    if raw_url and "postgresql+asyncpg://" in raw_url:
        raw_url = raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        config.set_main_option("sqlalchemy.url", raw_url)

    db_name = make_url(raw_url).database if raw_url else "unknown"
    print(f"alembic resolved_db={db_name} source={source}", flush=True)
    return raw_url, source


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url, _ = configure_url()
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
    configure_url()

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

