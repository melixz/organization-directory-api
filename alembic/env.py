from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

from src.database import Base  # Импортируем вашу базу
from src.models import *  # Убедитесь, что все модели импортированы

# Загружаем конфигурацию Alembic
config = context.config

# Читаем параметры конфигурации из alembic.ini
# и используем их для подключения к базе данных
fileConfig(config.config_file_name)

# Указываем метаданные для Alembic, чтобы он знал о ваших таблицах
target_metadata = Base.metadata

# URL подключения к базе данных
DATABASE_URL = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline():
    """
    Выполнение миграций в оффлайн-режиме (без подключения к базе).
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Выполнение миграций в онлайн-режиме (с подключением к базе).
    """
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


# Определяем режим выполнения миграции (онлайн или оффлайн)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
