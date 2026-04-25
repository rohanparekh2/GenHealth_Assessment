from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from db import get_db


router = APIRouter(prefix="/orders", tags=["orders"])


def _log_event(db: Session, action: str, entity_id: str | None, message: str):
    db.add(models.SystemLog(action=action, entity_id=entity_id, message=message))
    db.commit()


@router.post("", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    order = models.Order(**order_in.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    _log_event(
        db,
        action="CREATE_ORDER",
        entity_id=order.id,
        message=f"Created patient {order.patient_first_name} {order.patient_last_name}",
    )
    return order


@router.get("", response_model=list[schemas.OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).order_by(models.Order.id.desc()).all()


@router.get("/{id}", response_model=schemas.OrderRead)
def get_order(id: str, db: Session = Depends(get_db)):
    order = db.get(models.Order, id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.put("/{id}", response_model=schemas.OrderRead)
def update_order(id: str, order_in: schemas.OrderUpdate, db: Session = Depends(get_db)):
    order = db.get(models.Order, id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for field, value in order_in.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    db.add(order)
    db.commit()
    db.refresh(order)
    _log_event(
        db,
        action="UPDATE_ORDER",
        entity_id=order.id,
        message=f"Updated patient {order.patient_first_name} {order.patient_last_name}",
    )
    return order


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(id: str, db: Session = Depends(get_db)):
    order = db.get(models.Order, id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    patient_name = f"{order.patient_first_name} {order.patient_last_name}"
    db.delete(order)
    db.commit()
    _log_event(
        db,
        action="DELETE_ORDER",
        entity_id=id,
        message=f"Deleted patient {patient_name}",
    )
