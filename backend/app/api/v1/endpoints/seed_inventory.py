from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.seed_inventory import SeedInventory
from app.schemas.seed_inventory import (
    SeedInventoryCreate,
    SeedInventoryUpdate,
    SeedInventoryRead,
)

router = APIRouter()

#create a new seed inventory record
@router.post("/", response_model=SeedInventoryRead, status_code=status.HTTP_201_CREATED,)

def create_seed(payload: SeedInventoryCreate, db: Session = Depends(get_db),):
    seed = SeedInventory(**payload.model_dump())

    db.add(seed)
    db.commit()
    db.refresh(seed)

    return seed

#retrieve all seed inventory
@router.get("/", response_model=list[SeedInventoryRead],)

def list_seeds(crop_type: str | None = None, db: Session = Depends(get_db),):
    query = select(SeedInventory)

    if crop_type:
        query = query.where(SeedInventory.crop_type == crop_type)

    query = query.order_by(SeedInventory.id)

    return db.scalars(query).all()

#retrieve one seed record 

@router.get("/{seed_id}", response_model=SeedInventoryRead)

def get_seed(seed_id:int, db:Session = Depends(get_db)):
    seed = db.get(SeedInventory, seed_id)

    if seed is None:
        raise HTTPException(status_code=404, detail="Seed record not found")

    return seed

## Update an existing seed inventory record
@router.put("/{seed_id}", response_model=SeedInventoryRead)
def update_seed(
    seed_id: int,
    payload: SeedInventoryUpdate,
    db: Session = Depends(get_db),
):
    seed = db.get(SeedInventory, seed_id)

    if seed is None:
        raise HTTPException(
            status_code=404,
            detail="Seed record not found",
        )

    updates = payload.model_dump()

    if "crop_type" in updates and updates["crop_type"] is None:
        raise HTTPException(
            status_code=422,
            detail="Crop type cannot be null",
        )

    for field, value in updates.items():
        setattr(seed, field, value)

    db.commit()
    db.refresh(seed)

    return seed

#Delete a record

@router.delete("/{seed_id}", status_code=status.HTTP_204_NO_CONTENT)

def delete_seed(seed_id: int, db:Session = Depends(get_db)):
    seed = db.get(SeedInventory, seed_id)

    if seed is None:
        raise HTTPException(status_code=404, detail = "Seed record not found")

    db.delete(seed)
    db.commit()

