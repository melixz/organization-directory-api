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
    if activity_data.parent_id == 0:
        raise HTTPException(status_code=400, detail="parent_id=0 недопустим")
    if activity_data.parent_id is not None:
        parent_exists = await db.scalar(
            select(Activity.id).where(Activity.id == activity_data.parent_id)
        )
        if not parent_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Parent with id={activity_data.parent_id} does not exist",
            )

    new_activity = Activity(name=activity_data.name, parent_id=activity_data.parent_id)
    db.add(new_activity)
    await db.flush()
    await db.commit()
    await db.refresh(new_activity)

    stmt = (
        select(Activity)
        .where(Activity.id == new_activity.id)
        .options(selectinload(Activity.children).selectinload(Activity.children))
    )
    result = (await db.execute(stmt)).unique()
    loaded_activity = result.scalars().first()
    if not loaded_activity:
        raise HTTPException(status_code=404, detail="Activity not found after creation")
    return ActivityResponse(
        id=loaded_activity.id,
        name=loaded_activity.name,
        children=[
            {
                "id": ch.id,
                "name": ch.name,
                "children": [
                    {"id": grch.id, "name": grch.name} for grch in ch.children
                ],
            }
            for ch in loaded_activity.children
        ],
    )


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
    result = (await db.execute(stmt)).unique()
    activities = result.scalars().all()
    return [
        ActivityResponse(
            id=a.id,
            name=a.name,
            children=[
                {
                    "id": ch.id,
                    "name": ch.name,
                    "children": [
                        {"id": grch.id, "name": grch.name} for grch in ch.children
                    ],
                }
                for ch in a.children
            ],
        )
        for a in activities
    ]


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
    result = (await db.execute(stmt)).unique()
    activity = result.scalars().first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ActivityResponse(
        id=activity.id,
        name=activity.name,
        children=[
            {
                "id": ch.id,
                "name": ch.name,
                "children": [
                    {"id": grch.id, "name": grch.name} for grch in ch.children
                ],
            }
            for ch in activity.children
        ],
    )
