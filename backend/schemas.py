from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderBase(BaseModel):
    patient_first_name: str = Field(min_length=1, max_length=100)
    patient_last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    patient_first_name: str | None = Field(default=None, min_length=1, max_length=100)
    patient_last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class OrderRead(OrderBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
