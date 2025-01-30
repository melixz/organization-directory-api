from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import Building
from src.schemas import BuildingCreate, BuildingResponse
from src.dependencies import verify_api_key
from src.utils.geolocation import get_coordinates_from_city

router = APIRouter()


@router.get(
    "/",
    response_model=list[BuildingResponse],
    dependencies=[Depends(verify_api_key)],
    description="Получение списка всех зданий.",
)
async def list_buildings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Building))
    return result.scalars().all()


@router.get(
    "/{building_id}",
    response_model=BuildingResponse,
    dependencies=[Depends(verify_api_key)],
    description="Получение информации о здании по ID.",
)
async def get_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await db.get(Building, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.post(
    "/",
    response_model=BuildingResponse,
    dependencies=[Depends(verify_api_key)],
    description="Создание нового здания (адрес + автоматическое получение координат).",
)
async def create_building(
    building_data: BuildingCreate, db: AsyncSession = Depends(get_db)
):
    coords = await get_coordinates_from_city(building_data.address)
    if not coords:
        raise HTTPException(
            status_code=400, detail="Не удалось определить координаты по адресу"
        )
    lat, lon = coords
    new_building = Building(address=building_data.address, latitude=lat, longitude=lon)
    db.add(new_building)
    await db.commit()
    await db.refresh(new_building)
    return new_building
