from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import Building
from src.schemas import BuildingCreate, BuildingResponse

router = APIRouter()


@router.post("/", response_model=BuildingResponse)
async def create_building(
    building_data: BuildingCreate, db: AsyncSession = Depends(get_db)
):
    new_building = Building(**building_data.dict())
    db.add(new_building)
    await db.commit()
    await db.refresh(new_building)
    return new_building


@router.get("/", response_model=list[BuildingResponse])
async def list_buildings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Building))
    return result.scalars().all()


@router.get("/{building_id}", response_model=BuildingResponse)
async def get_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await db.get(Building, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building
