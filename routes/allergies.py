from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from schemas.schemas import AllergyCreate, AllergyUpdate, AllergyOut
from database.database import get_db
from database.models import Allergy, User
from services.auth_handler import get_current_user

router = APIRouter(prefix="/allergies", tags=["allergies"])

@router.get("", response_model=List[AllergyOut], include_in_schema=False)
@router.get("/", response_model=List[AllergyOut])
def get_user_allergies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieves all registered allergies for the authenticated user."""
    return db.query(Allergy).filter(Allergy.user_id == user.id).all()

@router.post("", response_model=AllergyOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=AllergyOut, status_code=status.HTTP_201_CREATED)
def add_user_allergy(
    allergy_in: AllergyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Registers a known drug or environmental allergy for the authenticated user."""
    new_allergy = Allergy(
        user_id=user.id,
        allergen=allergy_in.allergen.strip(),
        reaction=allergy_in.reaction.strip() if allergy_in.reaction else None,
        severity=allergy_in.severity.strip() if allergy_in.severity else "Moderate",
        verification_status=allergy_in.verification_status.strip() if allergy_in.verification_status else "Self-Reported"
    )
    db.add(new_allergy)
    db.commit()
    db.refresh(new_allergy)
    return new_allergy

@router.put("/{allergy_id}", response_model=AllergyOut)
def update_user_allergy(
    allergy_id: int,
    allergy_in: AllergyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Updates an existing allergy entry owned by the authenticated user."""
    allergy = db.query(Allergy).filter(
        Allergy.id == allergy_id,
        Allergy.user_id == user.id
    ).first()

    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy record not found or access denied."
        )

    if allergy_in.allergen is not None:
        clean_allergen = allergy_in.allergen.strip()
        if not clean_allergen:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Allergen name cannot be empty."
            )
        allergy.allergen = clean_allergen

    if allergy_in.reaction is not None:
        allergy.reaction = allergy_in.reaction.strip() if allergy_in.reaction else None

    if allergy_in.severity is not None:
        allergy.severity = allergy_in.severity.strip() if allergy_in.severity else None

    if allergy_in.verification_status is not None:
        allergy.verification_status = allergy_in.verification_status.strip()

    db.commit()
    db.refresh(allergy)
    return allergy

@router.delete("/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_allergy(
    allergy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Deletes an allergy entry owned by the authenticated user."""
    allergy = db.query(Allergy).filter(
        Allergy.id == allergy_id,
        Allergy.user_id == user.id
    ).first()

    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy record not found or access denied."
        )

    db.delete(allergy)
    db.commit()
    return None
