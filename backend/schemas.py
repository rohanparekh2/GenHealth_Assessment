from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderBase(BaseModel):
    patient_first_name: str = Field(min_length=1, max_length=100)
    patient_last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    patient_first_name: str | None = Field(default=None, min_length=1, max_length=100)
    patient_last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None


class OrderRead(OrderBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
