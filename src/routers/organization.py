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


def serialize_activity(activity, depth=3):
    if depth == 0:
        return {
            "id": activity.id,
            "name": activity.name,
            "children": [],
        }
    return {
        "id": activity.id,
        "name": activity.name,
        "children": [
            serialize_activity(child, depth=depth - 1) for child in activity.children
        ],
    }


def serialize_organization(org):
    return {
        "id": org.id,
        "name": org.name,
        "phone_numbers": org.phone_numbers.split(",") if org.phone_numbers else [],
        "building": {
            "id": org.building.id,
            "address": org.building.address,
            "latitude": org.building.latitude,
            "longitude": org.building.longitude,
        }
        if org.building
        else None,
        "activities": [serialize_activity(a) for a in org.activities],
    }


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
    min_lat: float = Query(None),
    max_lat: float = Query(None),
    min_lon: float = Query(None),
    max_lon: float = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if not (
        city
        or (
            (base_lat is not None and base_lon is not None and radius_km is not None)
            or (
                min_lat is not None
                and max_lat is not None
                and min_lon is not None
                and max_lon is not None
            )
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="At least one of 'city', 'base_lat, base_lon, radius_km' or 'min_lat, max_lat, min_lon, max_lon' must be provided.",
        )

    stmt = select(Organization).options(
        selectinload(Organization.building),
        selectinload(Organization.activities)
        .selectinload(Activity.children)
        .selectinload(Activity.children),
    )

    result = await db.execute(stmt)
    organizations = result.scalars().all()

    if (
        min_lat is not None
        and max_lat is not None
        and min_lon is not None
        and max_lon is not None
    ):
        organizations = [
            org
            for org in organizations
            if org.building
            and min_lat <= org.building.latitude <= max_lat
            and min_lon <= org.building.longitude <= max_lon
        ]

    if base_lat is not None and base_lon is not None and radius_km is not None:
        organizations = [
            org
            for org in organizations
            if org.building
            and calculate_distance(
                org.building.latitude, org.building.longitude, base_lat, base_lon
            )
            <= radius_km
        ]

    if city:
        organizations = [
            org
            for org in organizations
            if org.building and city.lower() in org.building.address.lower()
        ]

    return [
        OrganizationResponse(**serialize_organization(org)) for org in organizations
    ]


@router.get(
    "/",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
    description="Список всех организаций с необязательной фильтрацией по названию, виду деятельности и зданию.",
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    name: str = Query(None),
    activity_id: int = Query(None),
    building_id: int = Query(None),
):
    stmt = select(Organization).options(
        selectinload(Organization.building),
        selectinload(Organization.activities)
        .selectinload(Activity.children)
        .selectinload(Activity.children),
    )
    if name:
        stmt = stmt.where(Organization.name.ilike(f"%{name}%"))
    if activity_id:
        stmt = stmt.join(Organization.activities).where(Activity.id == activity_id)
    if building_id:
        stmt = stmt.where(Organization.building_id == building_id)

    result = await db.execute(stmt)
    organizations = result.scalars().all()

    return [OrganizationResponse(**serialize_organization(o)) for o in organizations]


@router.post(
    "/",
    response_model=OrganizationResponse,
    dependencies=[Depends(verify_api_key)],
    description="Создание новой организации.",
)
async def create_organization(
    org_data: OrganizationCreate, db: AsyncSession = Depends(get_db)
):
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
            selectinload(Organization.activities)
            .selectinload(Activity.children)
            .selectinload(Activity.children),
        )
    )
    result = await db.execute(stmt)
    loaded_org = result.scalars().first()

    if not loaded_org:
        raise HTTPException(
            status_code=404, detail="Organization not found after creation"
        )

    return OrganizationResponse(**serialize_organization(loaded_org))


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    dependencies=[Depends(verify_api_key)],
    description="Получение информации об организации по её идентификатору.",
)
async def get_organization(organization_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Organization)
        .where(Organization.id == organization_id)
        .options(
            selectinload(Organization.building),
            selectinload(Organization.activities)
            .selectinload(Activity.children)
            .selectinload(Activity.children),
        )
    )
    result = await db.execute(stmt)
    org = result.scalars().first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationResponse(**serialize_organization(org))
