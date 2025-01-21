from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import Organization, Activity, Building
from src.schemas import (
    OrganizationCreate,
    OrganizationResponse,
)
from src.utils.geolocation import get_coordinates_from_city
from src.utils.distance import calculate_distance
from src.dependencies import verify_api_key

router = APIRouter()


@router.post(
    "/", response_model=OrganizationResponse, dependencies=[Depends(verify_api_key)]
)
async def create_organization(
    org_data: OrganizationCreate, db: AsyncSession = Depends(get_db)
):
    """
    Создание новой организации.
    """
    new_org = Organization(
        name=org_data.name,
        phone_numbers=",".join(org_data.phone_numbers)
        if org_data.phone_numbers
        else None,
        building_id=org_data.building_id,
    )
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)

    if org_data.activity_ids:
        result = await db.execute(
            select(Activity).where(Activity.id.in_(org_data.activity_ids))
        )
        valid_activities = result.scalars().all()

        new_org.activities.extend(valid_activities)
        await db.commit()
        await db.refresh(new_org)

    return new_org


@router.get(
    "/",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    name: str = Query(None, description="Поиск по названию"),
    activity_id: int = Query(None, description="Фильтр по виду деятельности"),
):
    """
    Список организаций с фильтрацией по названию или виду деятельности.
    """
    query = select(Organization)

    if name:
        query = query.where(Organization.name.ilike(f"%{name}%"))
    if activity_id:
        query = query.join(Organization.activities).where(Activity.id == activity_id)

    result = await db.execute(query)
    organizations = result.scalars().unique().all()
    return organizations


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    """
    Получение информации об организации по ID.
    """
    organization = await db.get(Organization, org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.get(
    "/search",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
    description="Поиск организаций по координатам или названию города",
)
async def search_organizations(
    city: str = Query(None, description="Название города для поиска"),
    base_lat: float = Query(None, description="Широта базовой точки"),
    base_lon: float = Query(None, description="Долгота базовой точки"),
    radius_km: float = Query(None, description="Радиус поиска в километрах"),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск организаций по названию города или координатам с указанием радиуса поиска.
    """
    if city:
        coordinates = await get_coordinates_from_city(city)
        if not coordinates:
            raise HTTPException(status_code=404, detail=f"Город '{city}' не найден")
        base_lat, base_lon = coordinates

    if base_lat is None or base_lon is None:
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать либо название города, либо координаты (base_lat и base_lon).",
        )

    if radius_km is None:
        raise HTTPException(
            status_code=400, detail="Необходимо указать радиус поиска (radius_km)."
        )

    result = await db.execute(select(Organization).join(Building))
    organizations = result.scalars().all()

    nearby_organizations = [
        org
        for org in organizations
        if org.building
        and calculate_distance(
            org.building.latitude, org.building.longitude, base_lat, base_lon
        )
        <= radius_km
    ]

    return [OrganizationResponse.from_orm(org) for org in nearby_organizations]
