from fastapi import FastAPI
from src.routers import building, activity, organization

app = FastAPI(
    title="Organization Directory API",
    version="1.0.0",
    description="REST API для справочника организаций, зданий и видов деятельности",
)

app.include_router(building.router, prefix="/buildings", tags=["Buildings"])
app.include_router(activity.router, prefix="/activities", tags=["Activities"])
app.include_router(organization.router, prefix="/organizations", tags=["Organizations"])
