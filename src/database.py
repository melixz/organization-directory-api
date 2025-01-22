from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

Base = declarative_base()

# Создание асинхронного двигателя и фабрики сессий
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Запрет истечения атрибутов
)


async def get_db():
    """
    Генератор для получения сессии базы данных.
    """
    async with async_session_factory() as session:
        yield session
