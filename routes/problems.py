from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from schemas.schemas import ProblemCreate, ProblemOut
from database.database import get_db
from database.models import RecentProblem, User
from services.auth_handler import get_current_user

router = APIRouter(prefix="/problems", tags=["problems"])

def infer_problem_category(text: str) -> str:
    """Classifies natural language health complaints into standard medical categories."""
    t = text.lower()
    if any(k in t for k in ["chest", "heart", "palpitat", "angina", "pulse", "tachycardia"]):
        return "Cardiovascular"
    if any(k in t for k in ["breath", "shortness", "dyspnea", "cough", "wheez", "lung"]):
        return "Respiratory"
    if any(k in t for k in ["headache", "dizz", "faint", "migraine", "seizure", "numb", "syncope"]):
        return "Neurological"
    if any(k in t for k in ["stomach", "nausea", "vomit", "acid", "abdominal", "diarrhea", "peptic"]):
        return "Gastrointestinal"
    if any(k in t for k in ["sugar", "glucose", "thirst", "insulin", "diabetes"]):
        return "Endocrine / Metabolic"
    if any(k in t for k in ["fever", "temperature", "chill", "infection", "sweat"]):
        return "Systemic / Infectious"
    if any(k in t for k in ["joint", "muscle", "back", "knee", "bone", "ache"]):
        return "Musculoskeletal"
    return "General Health"

@router.get("", response_model=List[ProblemOut], include_in_schema=False)
@router.get("/", response_model=List[ProblemOut])
def list_user_problems(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieves all logged symptoms and recent problems for the authenticated user."""
    return db.query(RecentProblem).filter(RecentProblem.user_id == user.id).order_by(RecentProblem.created_at.desc()).all()

@router.post("", response_model=ProblemOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
def create_user_problem(
    problem_in: ProblemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Logs a new natural language health problem or symptom for the authenticated user."""
    category = problem_in.problem_category
    if not category or not category.strip():
        category = infer_problem_category(problem_in.problem_text)

    new_problem = RecentProblem(
        user_id=user.id,
        problem_text=problem_in.problem_text.strip(),
        problem_category=category.strip(),
        severity=problem_in.severity.strip() if problem_in.severity else "Moderate",
        duration=problem_in.duration.strip() if problem_in.duration else None,
        status=problem_in.status.strip() if problem_in.status else "Active",
        notes=problem_in.notes.strip() if problem_in.notes else None
    )
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    return new_problem

@router.put("/{problem_id}", response_model=ProblemOut)
def update_user_problem(
    problem_id: int,
    problem_update: ProblemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Updates an existing symptom record owned by the authenticated user."""
    problem = db.query(RecentProblem).filter(
        RecentProblem.id == problem_id,
        RecentProblem.user_id == user.id
    ).first()

    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem record not found.")

    if problem_update.problem_text:
        problem.problem_text = problem_update.problem_text.strip()
        problem.problem_category = problem_update.problem_category or infer_problem_category(problem.problem_text)
    if problem_update.severity:
        problem.severity = problem_update.severity.strip()
    if problem_update.duration is not None:
        problem.duration = problem_update.duration.strip() if problem_update.duration else None
    if problem_update.status:
        problem.status = problem_update.status.strip()
    if problem_update.notes is not None:
        problem.notes = problem_update.notes.strip() if problem_update.notes else None

    db.commit()
    db.refresh(problem)
    return problem

@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Deletes a problem entry owned by the authenticated user."""
    problem = db.query(RecentProblem).filter(
        RecentProblem.id == problem_id,
        RecentProblem.user_id == user.id
    ).first()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem record not found or access denied."
        )

    db.delete(problem)
    db.commit()
    return None
