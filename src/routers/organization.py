from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import Organization, Activity
from src.schemas import (
    OrganizationCreate,
    OrganizationResponse,
)

router = APIRouter()


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate, db: AsyncSession = Depends(get_db)
):
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


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    name: str = Query(None, description="Поиск по названию"),
    activity_id: int = Query(None, description="Фильтр по виду деятельности"),
):
    query = select(Organization)

    if name:
        query = query.where(Organization.name.ilike(f"%{name}%"))
    if activity_id:
        query = query.join(Organization.activities).where(Activity.id == activity_id)

    result = await db.execute(query)
    organizations = result.scalars().unique().all()
    return organizations


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    organization = await db.get(Organization, org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization
