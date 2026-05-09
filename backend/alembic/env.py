import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with sync URL from env
database_url_sync = os.environ.get("DATABASE_URL_SYNC", "")
if database_url_sync:
    config.set_main_option("sqlalchemy.url", database_url_sync)

# Import all models so autogenerate can detect them
from app.models.base import Base  # noqa: E402
from app.models.user import User, Profile, Portfolio  # noqa: E402
from app.models.order import Order, Application  # noqa: E402
from app.models.contract import Contract, ContractClause, Milestone, Deliverable  # noqa: E402
from app.models.escrow import EscrowTransaction  # noqa: E402
from app.models.dispute import Dispute, DisputeMessage  # noqa: E402
from app.models.review import Review  # noqa: E402
from app.models.notification import Notification  # noqa: E402
from app.models.audit import AuditLog  # noqa: E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
