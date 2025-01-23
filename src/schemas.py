from typing import Optional, List
from pydantic import BaseModel, Field, field_serializer, ConfigDict


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

    @field_serializer("phone_numbers")
    def deserialize_phone_numbers(self, value: Optional[str]) -> List[str]:
        """
        Преобразует строку, разделённую запятыми, в список.
        Если `None`, возвращает пустой список.
        """
        if isinstance(value, str):
            return value.split(",")
        return []
