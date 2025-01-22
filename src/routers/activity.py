from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.database import get_db
from src.models import Activity
from src.schemas import ActivityCreate, ActivityResponse
from src.dependencies import verify_api_key

router = APIRouter()


@router.post(
    "/", response_model=ActivityResponse, dependencies=[Depends(verify_api_key)]
)
async def create_activity(
    activity_data: ActivityCreate, db: AsyncSession = Depends(get_db)
):
    new_activity = Activity(**activity_data.dict())
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return ActivityResponse.from_orm(new_activity)


@router.get(
    "/", response_model=list[ActivityResponse], dependencies=[Depends(verify_api_key)]
)
async def list_activities(db: AsyncSession = Depends(get_db)):
    stmt = select(Activity).options(selectinload(Activity.children))
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [ActivityResponse.from_orm(item) for item in items]


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Activity)
        .where(Activity.id == activity_id)
        .options(selectinload(Activity.children))
    )
    result = await db.execute(stmt)
    activity = result.scalars().first()
    if not activity:
        raise HTTPException(status_code=404, detail="Not found")
    return ActivityResponse.from_orm(activity)
