import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from src.database import Base  # Ваши метаданные
from src.models import *  # Импорты моделей

# Загружаем конфигурацию Alembic
config = context.config

# Указываем метаданные для Alembic
target_metadata = Base.metadata

# Получаем DATABASE_URL из переменных окружения
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL")
if not ASYNC_DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Преобразуем асинхронный URL в синхронный
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)

# Обновляем sqlalchemy.url в конфигурации Alembic
config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)

# Настройка логирования
fileConfig(config.config_file_name)


def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме."""
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Запуск миграций в онлайн-режиме."""
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
