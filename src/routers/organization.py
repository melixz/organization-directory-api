from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from src.database import get_db
from src.models import Organization, Activity
from src.schemas import OrganizationResponse
from src.dependencies import verify_api_key


router = APIRouter()


def organization_to_dict(org):
    """
    Преобразует объект Organization в словарь с полностью загруженными данными.
    """
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
        "activities": [
            {
                "id": activity.id,
                "name": activity.name,
                "children": [
                    {"id": child.id, "name": child.name} for child in activity.children
                ],
            }
            for activity in org.activities
        ],
    }


@router.get(
    "/",
    response_model=list[OrganizationResponse],
    dependencies=[Depends(verify_api_key)],
    description="Получение списка всех организаций.",
)
async def list_organizations(db: AsyncSession = Depends(get_db)):
    stmt = select(Organization).options(
        selectinload(Organization.building),
        selectinload(Organization.activities).selectinload(Activity.children),
    )
    result = await db.execute(stmt)
    organizations = result.scalars().all()

    # Преобразуем объекты Organization в словари
    organizations_data = [organization_to_dict(org) for org in organizations]
    return [OrganizationResponse(**data) for data in organizations_data]


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
            selectinload(Organization.activities).selectinload(Activity.children),
        )
    )
    result = await db.execute(stmt)
    org = result.scalars().first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Преобразуем объект Organization в словарь
    org_data = organization_to_dict(org)
    return OrganizationResponse(**org_data)
