from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BuildingBase(BaseModel):
    address: str
    latitude: float
    longitude: float


class BuildingCreate(BuildingBase):
    pass


class BuildingResponse(BuildingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ActivityCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class ActivityResponse(BaseModel):
    id: int
    name: str
    children: List["ActivityResponse"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            name=obj.name,
            children=[
                cls.from_orm(child) for child in getattr(obj, "children", []) or []
            ],
        )


ActivityResponse.model_rebuild()


class OrganizationBase(BaseModel):
    name: str
    phone_numbers: List[str] = Field(default_factory=list)


class OrganizationCreate(OrganizationBase):
    building_id: Optional[int] = None
    activity_ids: List[int] = Field(default_factory=list)


class OrganizationResponse(OrganizationBase):
    id: int
    building: Optional[BuildingResponse]
    activities: List[ActivityResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            name=obj.name,
            phone_numbers=(
                obj.phone_numbers.split(",")
                if obj.phone_numbers and isinstance(obj.phone_numbers, str)
                else []
            ),
            building=(
                BuildingResponse.model_validate(obj.building) if obj.building else None
            ),
            activities=[ActivityResponse.from_orm(a) for a in (obj.activities or [])],
        )
