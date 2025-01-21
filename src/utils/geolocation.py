import httpx
from typing import Optional, Tuple

NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"


async def get_coordinates_from_city(city: str) -> Optional[Tuple[float, float]]:
    """
    Получение координат (широты и долготы) для указанного города через Nominatim API.
    """
    params = {
        "q": city,
        "format": "json",
        "limit": 1,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(NOMINATIM_API_URL, params=params)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            latitude = float(data["lat"])
            longitude = float(data["lon"])
            return latitude, longitude
    return None
