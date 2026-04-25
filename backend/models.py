import uuid

from sqlalchemy import Column, Date, DateTime, Integer, String, func

from db import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    patient_first_name = Column(String(100), nullable=False)
    patient_last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_path = Column(String(255), nullable=False)
    http_method = Column(String(10), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    action = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    message = Column(String(255), nullable=False)
