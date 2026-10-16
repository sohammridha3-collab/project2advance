from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User, HealthAssessment, Prescription, RecentProblem, Allergy
from schemas.schemas import (
    AssessmentHistoryOut, PrescriptionOut, ProblemOut, AllergyOut,
    ProblemCreate, AllergyCreate, PrescriptionCreate
)
from services.auth_handler import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/history", response_model=List[AssessmentHistoryOut])
def get_prediction_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(HealthAssessment)
        .filter(HealthAssessment.user_id == user.id)
        .order_by(HealthAssessment.created_at.desc())
        .all()
    )

@router.get("/me/prescriptions", response_model=List[PrescriptionOut])
def get_prescriptions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(Prescription)
        .filter(Prescription.user_id == user.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )

@router.post("/me/prescriptions", response_model=PrescriptionOut)
def add_prescription(
    prescription: PrescriptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_prescription = Prescription(
        user_id=user.id,
        doctor_name=prescription.doctor_name,
        hospital_name=prescription.hospital_name,
        prescription_date=prescription.prescription_date,
        diagnosis=prescription.diagnosis,
        notes=prescription.notes
    )
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)
    return new_prescription

@router.get("/me/problems", response_model=List[ProblemOut])
def get_problems(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(RecentProblem)
        .filter(RecentProblem.user_id == user.id)
        .order_by(RecentProblem.created_at.desc())
        .all()
    )

@router.post("/me/problems", response_model=ProblemOut)
def add_problem(
    problem: ProblemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_problem = RecentProblem(
        user_id=user.id,
        problem_text=problem.problem_text,
        problem_category=problem.problem_category,
        severity=problem.severity,
        duration=problem.duration
    )
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    return new_problem

@router.get("/me/allergies", response_model=List[AllergyOut])
def get_allergies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Allergy).filter(Allergy.user_id == user.id).all()

@router.post("/me/allergies", response_model=AllergyOut)
def add_allergy(
    allergy: AllergyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_allergy = Allergy(
        user_id=user.id,
        allergen=allergy.allergen,
        reaction=allergy.reaction,
        severity=allergy.severity
    )
    db.add(new_allergy)
    db.commit()
    db.refresh(new_allergy)
    return new_allergy
