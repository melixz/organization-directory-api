from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database import get_db
from src.models import Activity
from src.schemas import ActivityCreate, ActivityResponse
from src.dependencies import verify_api_key

router = APIRouter()


def activity_to_dict(activity):
    return {
        "id": activity.id,
        "name": activity.name,
        "children": [
            {
                "id": child.id,
                "name": child.name,
                "children": [
                    {"id": grandchild.id, "name": grandchild.name}
                    for grandchild in child.children
                ],
            }
            for child in activity.children
        ],
    }


@router.post(
    "/",
    response_model=ActivityResponse,
    dependencies=[Depends(verify_api_key)],
    description="Создание нового вида деятельности.",
)
async def create_activity(
    activity_data: ActivityCreate, db: AsyncSession = Depends(get_db)
):
    new_activity = Activity(**activity_data.dict())
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)

    stmt = (
        select(Activity)
        .where(Activity.id == new_activity.id)
        .options(selectinload(Activity.children).selectinload(Activity.children))
    )
    result = await db.execute(stmt)
    loaded_activity = result.scalars().first()

    if not loaded_activity:
        raise HTTPException(status_code=404, detail="Activity not found after creation")

    activity_data = activity_to_dict(loaded_activity)
    return ActivityResponse(**activity_data)


@router.get(
    "/",
    response_model=list[ActivityResponse],
    dependencies=[Depends(verify_api_key)],
    description="Получение списка всех видов деятельности.",
)
async def list_activities(db: AsyncSession = Depends(get_db)):
    stmt = select(Activity).options(
        selectinload(Activity.children).selectinload(Activity.children)
    )
    result = await db.execute(stmt)
    activities = result.scalars().all()

    activities_data = [activity_to_dict(activity) for activity in activities]
    return [ActivityResponse(**data) for data in activities_data]


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    dependencies=[Depends(verify_api_key)],
    description="Получение информации о виде деятельности по ID.",
)
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Activity)
        .where(Activity.id == activity_id)
        .options(selectinload(Activity.children).selectinload(Activity.children))
    )
    result = await db.execute(stmt)
    activity = result.scalars().first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity_data = activity_to_dict(activity)
    return ActivityResponse(**activity_data)
