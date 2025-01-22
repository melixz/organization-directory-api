import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from src.database import async_session_factory
from src.models import Organization, Building, Activity


async def create_mock_data():
    """
    Основная функция для создания тестовых данных.
    Последовательно вызывает функции создания зданий, активностей и организаций.
    """
    async with async_session_factory() as session:
        await create_buildings(session)
        await create_activities(session)
        await create_organizations(session)


async def create_buildings(session: AsyncSession):
    """
    Создает записи зданий в базе данных.

    Args:
        session (AsyncSession): Сессия для взаимодействия с базой данных.
    """
    buildings = [
        Building(
            address="Москва, Ленина 1, офис 3", latitude=55.7558, longitude=37.6173
        ),
        Building(
            address="Санкт-Петербург, Невский проспект, д. 22",
            latitude=59.9343,
            longitude=30.3351,
        ),
    ]
    session.add_all(buildings)
    await session.commit()


async def create_activities(session: AsyncSession):
    """
    Создает записи активностей в базе данных, включая родительские и дочерние активности.

    Args:
        session (AsyncSession): Сессия для взаимодействия с базой данных.
    """
    parent_activities = [
        Activity(name="Еда"),
        Activity(name="Автомобили"),
    ]
    session.add_all(parent_activities)
    await session.commit()

    result = await session.execute(
        select(Activity).where(Activity.name.in_(["Еда", "Автомобили"]))
    )
    parent_activities_dict = {
        activity.name: activity.id for activity in result.scalars().all()
    }

    child_activities = [
        Activity(name="Мясная продукция", parent_id=parent_activities_dict["Еда"]),
        Activity(name="Молочная продукция", parent_id=parent_activities_dict["Еда"]),
        Activity(name="Грузовые", parent_id=parent_activities_dict["Автомобили"]),
        Activity(name="Легковые", parent_id=parent_activities_dict["Автомобили"]),
    ]
    session.add_all(child_activities)
    await session.commit()


async def create_organizations(session: AsyncSession):
    """
    Создает записи организаций в базе данных и привязывает к ним активности.

    Args:
        session (AsyncSession): Сессия для взаимодействия с базой данных.
    """
    buildings = (await session.execute(select(Building))).scalars().all()
    activities = (await session.execute(select(Activity))).scalars().all()

    organizations = [
        Organization(
            name="ООО Рога и Копыта",
            phone_numbers=", ".join(["2-222-222", "3-333-333"]),
            building_id=buildings[0].id,
        ),
        Organization(
            name="ИП Пример",
            phone_numbers=", ".join(["8-800-555-35-35"]),
            building_id=buildings[1].id,
        ),
    ]
    session.add_all(organizations)
    await session.commit()

    organizations = (
        (
            await session.execute(
                select(Organization).options(selectinload(Organization.activities))
            )
        )
        .scalars()
        .all()
    )
    for org in organizations:
        org.activities.extend(activities[:2])
    await session.commit()


if __name__ == "__main__":
    """
    Точка входа для выполнения создания тестовых данных.
    """
    asyncio.run(create_mock_data())
