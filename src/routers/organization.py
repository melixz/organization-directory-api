from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import Organization, Activity, Building
from src.schemas import OrganizationCreate, OrganizationResponse
from src.dependencies import verify_api_key

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
    if org_data.building_id:
        building_exists = await db.scalar(
            select(Building.id).where(Building.id == org_data.building_id)
        )
        if not building_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Building with id {org_data.building_id} does not exist.",
            )

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
        for activity in valid_activities:
            new_org.activities.append(activity)
        await db.commit()

    org_dict = {
        "id": new_org.id,
        "name": new_org.name,
        "phone_numbers": new_org.phone_numbers.split(",")
        if new_org.phone_numbers
        else [],
        "building": None,
        "activities": [],
    }

    if new_org.building_id:
        building = await db.get(Building, new_org.building_id)
        if building:
            org_dict["building"] = {
                "id": building.id,
                "address": building.address,
                "latitude": building.latitude,
                "longitude": building.longitude,
            }

    # Добавляем данные о видах деятельности
    result = await db.execute(
        select(Activity).where(Activity.id.in_([a.id for a in new_org.activities]))
    )
    activities = result.scalars().all()
    org_dict["activities"] = [
        {"id": activity.id, "name": activity.name} for activity in activities
    ]

    return OrganizationResponse(**org_dict)


@router.get(
    "/",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
    description="Список всех организаций с фильтрацией.",
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    name: str = Query(None, description="Поиск по названию"),
    activity_id: int = Query(None, description="Фильтр по виду деятельности"),
):
    stmt = select(Organization)
    if name:
        stmt = stmt.where(Organization.name.ilike(f"%{name}%"))
    result = await db.execute(stmt)
    organizations = result.scalars().all()

    org_list = []
    for org in organizations:
        org_dict = {
            "id": org.id,
            "name": org.name,
            "phone_numbers": org.phone_numbers.split(",") if org.phone_numbers else [],
            "building": None,
            "activities": [],
        }

        # Добавляем данные о здании
        if org.building_id:
            building = await db.get(Building, org.building_id)
            if building:
                org_dict["building"] = {
                    "id": building.id,
                    "address": building.address,
                    "latitude": building.latitude,
                    "longitude": building.longitude,
                }

        result = await db.execute(
            select(Activity).where(Activity.id.in_([a.id for a in org.activities]))
        )
        activities = result.scalars().all()
        org_dict["activities"] = [
            {"id": activity.id, "name": activity.name} for activity in activities
        ]

        org_list.append(org_dict)

    return [OrganizationResponse(**data) for data in org_list]


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    dependencies=[Depends(verify_api_key)],
    description="Получение информации об организации по её идентификатору.",
)
async def get_organization(organization_id: int, db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org_dict = {
        "id": org.id,
        "name": org.name,
        "phone_numbers": org.phone_numbers.split(",") if org.phone_numbers else [],
        "building": None,
        "activities": [],
    }

    if org.building_id:
        building = await db.get(Building, org.building_id)
        if building:
            org_dict["building"] = {
                "id": building.id,
                "address": building.address,
                "latitude": building.latitude,
                "longitude": building.longitude,
            }

    result = await db.execute(
        select(Activity).where(Activity.id.in_([a.id for a in org.activities]))
    )
    activities = result.scalars().all()
    org_dict["activities"] = [
        {"id": activity.id, "name": activity.name} for activity in activities
    ]

    return OrganizationResponse(**org_dict)
