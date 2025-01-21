from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import Activity
from src.schemas import ActivityCreate, ActivityResponse

router = APIRouter()


@router.post("/", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate, db: AsyncSession = Depends(get_db)
):
    new_activity = Activity(**activity_data.dict())
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity


@router.get("/", response_model=list[ActivityResponse])
async def list_activities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity))
    return result.scalars().all()


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    activity = await db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity
