from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from src.database import get_db
from src.models import Organization, Activity, Building
from src.schemas import OrganizationCreate, OrganizationResponse
from src.dependencies import verify_api_key
from src.utils.distance import calculate_distance

router = APIRouter()


@router.post(
    "/",
    response_model=OrganizationResponse,
    dependencies=[Depends(verify_api_key)],
    description="Создание новой организации.",
)
async def create_organization(
    org_data: OrganizationCreate, db: AsyncSession = Depends(get_db)
):
    """
    Создание новой организации с привязкой к зданию и активностям.
    """
    async with db.begin():
        building = None
        if org_data.building_id:
            building = await db.scalar(
                select(Building).where(Building.id == org_data.building_id)
            )
            if not building:
                raise HTTPException(
                    status_code=400,
                    detail=f"Building with id {org_data.building_id} does not exist.",
                )

        activities = []
        if org_data.activity_ids:
            result = await db.execute(
                select(Activity).where(Activity.id.in_(org_data.activity_ids))
            )
            activities = result.scalars().all()

            if len(activities) != len(org_data.activity_ids):
                raise HTTPException(
                    status_code=400,
                    detail="One or more activities do not exist.",
                )

        # Создаём новую организацию
        new_org = Organization(
            name=org_data.name,
            phone_numbers=",".join(org_data.phone_numbers)
            if org_data.phone_numbers
            else None,
            building=building,
            activities=activities,
        )
        db.add(new_org)
        await db.flush()
        await db.refresh(new_org)

    stmt = (
        select(Organization)
        .where(Organization.id == new_org.id)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities).selectinload(Activity.children),
            selectinload(Organization.activities)
            .selectinload(Activity.children)
            .selectinload(Activity.children),
        )
    )
    result = await db.execute(stmt)
    loaded_org = result.scalars().first()

    org_dict = {
        "id": loaded_org.id,
        "name": loaded_org.name,
        "phone_numbers": loaded_org.phone_numbers.split(",")
        if loaded_org.phone_numbers
        else [],
        "building": loaded_org.building,
        "activities": loaded_org.activities,
    }
    return OrganizationResponse(**org_dict)


@router.get(
    "/",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
    description="Список всех организаций с фильтрацией.",
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    name: str = Query(None),
    activity_id: int = Query(None),
):
    """
    Получение списка всех организаций с фильтрацией по названию или активности.
    """
    stmt = select(Organization).options(
        selectinload(Organization.building),
        selectinload(Organization.activities).selectinload(Activity.children),
    )
    if name:
        stmt = stmt.where(Organization.name.ilike(f"%{name}%"))
    if activity_id:
        stmt = stmt.join(Organization.activities).where(Activity.id == activity_id)

    result = await db.execute(stmt)
    organizations = result.scalars().all()

    org_list = []
    for org in organizations:
        org_dict = {
            "id": org.id,
            "name": org.name,
            "phone_numbers": org.phone_numbers.split(",") if org.phone_numbers else [],
            "building": org.building,
            "activities": org.activities,
        }
        org_list.append(OrganizationResponse(**org_dict))

    return org_list


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    dependencies=[Depends(verify_api_key)],
    description="Получение информации об организации по её идентификатору.",
)
async def get_organization(organization_id: int, db: AsyncSession = Depends(get_db)):
    """
    Получение одной организации по её ID.
    """
    stmt = (
        select(Organization)
        .where(Organization.id == organization_id)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities).selectinload(Activity.children),
        )
    )
    result = await db.execute(stmt)
    org = result.scalars().first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org_dict = {
        "id": org.id,
        "name": org.name,
        "phone_numbers": org.phone_numbers.split(",") if org.phone_numbers else [],
        "building": org.building,
        "activities": org.activities,
    }
    return OrganizationResponse(**org_dict)


@router.get(
    "/search",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
    description="Поиск организаций по координатам или названию города.",
)
async def search_organizations(
    city: str = Query(None),
    base_lat: float = Query(None),
    base_lon: float = Query(None),
    radius_km: float = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск организаций по городу или координатам.
    """
    stmt = select(Organization).options(selectinload(Organization.building))
    result = await db.execute(stmt)
    organizations = result.scalars().all()

    if base_lat is not None and base_lon is not None and radius_km is not None:
        nearby_organizations = [
            org
            for org in organizations
            if org.building
            and calculate_distance(
                org.building.latitude, org.building.longitude, base_lat, base_lon
            )
            <= radius_km
        ]
        org_list = []
        for org in nearby_organizations:
            org_dict = {
                "id": org.id,
                "name": org.name,
                "phone_numbers": org.phone_numbers.split(",")
                if org.phone_numbers
                else [],
                "building": org.building,
                "activities": org.activities,
            }
            org_list.append(OrganizationResponse(**org_dict))
        return org_list

    org_list = []
    for org in organizations:
        org_dict = {
            "id": org.id,
            "name": org.name,
            "phone_numbers": org.phone_numbers.split(",") if org.phone_numbers else [],
            "building": org.building,
            "activities": org.activities,
        }
        org_list.append(OrganizationResponse(**org_dict))
    return org_list
