from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from schemas.schemas import (
    MedicineOut, MedicineCreate, MedicineCheckRequest, MedicineCheckResponse
)
from database.database import get_db
from database.models import Medicine
from services.medicine_safety import check_medicine_safety

router = APIRouter(prefix="/medicines", tags=["medicines"])

@router.get("", response_model=List[MedicineOut], include_in_schema=False)
@router.get("/", response_model=List[MedicineOut])
def list_medicines(
    search: Optional[str] = Query(None, description="Search by name or category"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists medicines in the database with optional search filtering."""
    query = db.query(Medicine)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Medicine.medicine_name.ilike(term)) | 
            (Medicine.generic_name.ilike(term)) |
            (Medicine.category.ilike(term))
        )
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=MedicineOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=MedicineOut, status_code=status.HTTP_201_CREATED)
def create_medicine(
    medicine_in: MedicineCreate,
    db: Session = Depends(get_db)
):
    """Adds a new medicine specification to the database catalog."""
    existing = db.query(Medicine).filter(Medicine.medicine_name.ilike(medicine_in.medicine_name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Medicine '{medicine_in.medicine_name}' already exists."
        )

    new_med = Medicine(**medicine_in.model_dump())
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    return new_med

@router.get("/{medicine_id}", response_model=MedicineOut)
def get_medicine(
    medicine_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves medicine details by ID."""
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")
    return med

@router.post("/check-safety", response_model=MedicineCheckResponse)
def evaluate_medicine_safety(
    request: MedicineCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates safety warnings, contraindications, and drug interactions for a target medicine.
    Checks against specified patient conditions and existing medications.
    """
    safety_result = check_medicine_safety(
        medicine_name=request.medicine_name,
        patient_conditions=request.patient_conditions or [],
        current_meds=request.current_meds or [],
        db=db
    )

    db_medicine = db.query(Medicine).filter(Medicine.medicine_name.ilike(request.medicine_name.strip())).first()

    return {
        "medicine_name": request.medicine_name,
        "medicine_info": db_medicine,
        "safety_warnings": safety_result["safety_warnings"],
        "interactions": safety_result["interactions"],
        "contraindications": safety_result["contraindications"],
        "allergy_warnings": safety_result["allergy_warnings"],
        "professional_consultation_required": safety_result["professional_consultation_required"]
    }
