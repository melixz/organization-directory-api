from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Building Schemas
class BuildingBase(BaseModel):
    """
    Базовая схема для данных о здании.
    """

    address: str
    latitude: float
    longitude: float


class BuildingCreate(BuildingBase):
    """
    Схема для создания здания.
    """

    pass


class BuildingResponse(BuildingBase):
    """
    Схема для отображения данных о здании.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


# Activity Schemas
class ActivityCreate(BaseModel):
    """
    Схема для создания вида деятельности.
    """

    name: str
    parent_id: Optional[int] = None


class ActivityResponse(BaseModel):
    """
    Схема для отображения данных о виде деятельности.
    """

    id: int
    name: str
    children: List["ActivityResponse"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """
        Метод для преобразования ORM-модели в схему.
        """
        return cls(
            id=obj.id,
            name=obj.name,
            children=[
                cls.from_orm(child) for child in getattr(obj, "children", []) or []
            ],
        )


ActivityResponse.model_rebuild()


# Organization Schemas
class OrganizationBase(BaseModel):
    """
    Базовая схема для данных об организации.
    """

    name: str
    phone_numbers: List[str] = Field(default_factory=list)


class OrganizationCreate(OrganizationBase):
    """
    Схема для создания организации.
    """

    building_id: Optional[int] = None
    activity_ids: List[int] = Field(default_factory=list)


class OrganizationResponse(OrganizationBase):
    """
    Схема для отображения данных об организации.
    """

    id: int
    building: Optional[BuildingResponse]
    activities: List[ActivityResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """
        Метод для преобразования ORM-модели в схему.
        """
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
