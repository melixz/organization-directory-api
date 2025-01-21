from pydantic import BaseModel, Field
from typing import Optional, List


class BuildingBase(BaseModel):
    address: str
    latitude: float
    longitude: float


class BuildingCreate(BuildingBase):
    pass


class BuildingResponse(BuildingBase):
    id: int

    class Config:
        orm_mode = True


class ActivityBase(BaseModel):
    name: str = Field(..., min_length=1)


class ActivityCreate(ActivityBase):
    parent_id: Optional[int] = None


class ActivityResponse(ActivityBase):
    id: int
    children: List["ActivityResponse"] = []

    class Config:
        orm_mode = True


class OrganizationBase(BaseModel):
    name: str
    phone_numbers: List[str] = []


class OrganizationCreate(OrganizationBase):
    building_id: Optional[int] = None
    activity_ids: List[int] = []


class OrganizationResponse(OrganizationBase):
    id: int
    building: Optional[BuildingResponse]
    activities: List[ActivityResponse] = []

    class Config:
        orm_mode = True
