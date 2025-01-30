from fastapi import FastAPI
from src.routers.v1 import (
    building as building_v1,
    activity as activity_v1,
    organization as organization_v1,
)

app = FastAPI(
    title="Organization Directory API",
    version="1.0.0",
    description="REST API для справочника организаций, зданий и видов деятельности",
)

app.include_router(
    building_v1.router, prefix="/api/v1/buildings", tags=["Buildings v1"]
)
app.include_router(
    activity_v1.router, prefix="/api/v1/activities", tags=["Activities v1"]
)
app.include_router(
    organization_v1.router, prefix="/api/v1/organizations", tags=["Organizations v1"]
)
