"""
Doctor-Visit Briefing & Consent-Based Sharing Routes for HealthBridge AI
"""
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.database import get_db
from database.models import User, DoctorBriefing, SharedBriefing
from services.auth_handler import get_current_user
from services.context_engine import generate_doctor_briefing_draft
from schemas.schemas import (
    DoctorBriefingCreate, DoctorBriefingUpdate, DoctorBriefingOut,
    ShareBriefingCreate, SharedBriefingOut, PublicSharedBriefingOut
)

router = APIRouter(prefix="/briefings", tags=["Doctor Briefings"])

@router.get("", response_model=List[DoctorBriefingOut])
def list_user_briefings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all saved doctor visit briefings for the authenticated patient."""
    briefings = db.query(DoctorBriefing).filter(
        DoctorBriefing.user_id == current_user.id
    ).order_by(desc(DoctorBriefing.created_at)).all()
    return briefings

@router.post("/draft")
async def draft_briefing(
    request: Request,
    visit_reason: Optional[str] = Query(None, description="Reason for the clinical visit"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synthesizes an automated draft briefing based on the patient's actual recorded health data.
    Accepts visit_reason via query string or JSON payload.
    """
    reason = visit_reason
    if not reason:
        try:
            body = await request.json()
            if isinstance(body, dict):
                reason = body.get("visit_reason")
        except Exception:
            pass
    if not reason:
        reason = "Routine Health Consultation"
    return generate_doctor_briefing_draft(user_id=current_user.id, visit_reason=reason, db=db)

@router.post("", response_model=DoctorBriefingOut, status_code=status.HTTP_201_CREATED)
def create_briefing(
    payload: DoctorBriefingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Saves a new doctor visit briefing."""
    briefing = DoctorBriefing(
        user_id=current_user.id,
        title=payload.title.strip(),
        visit_reason=payload.visit_reason.strip(),
        symptoms_summary=payload.symptoms_summary,
        vitals_summary=payload.vitals_summary,
        allergies_summary=payload.allergies_summary,
        medicines_summary=payload.medicines_summary,
        questions_to_ask=payload.questions_to_ask,
        notes=payload.notes
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)
    return briefing

@router.get("/{briefing_id}", response_model=DoctorBriefingOut)
def get_briefing(
    briefing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves a specific doctor visit briefing owned by the authenticated patient."""
    briefing = db.query(DoctorBriefing).filter(
        DoctorBriefing.id == briefing_id,
        DoctorBriefing.user_id == current_user.id
    ).first()
    if not briefing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found.")
    return briefing

@router.put("/{briefing_id}", response_model=DoctorBriefingOut)
def update_briefing(
    briefing_id: int,
    payload: DoctorBriefingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates an existing doctor visit briefing."""
    briefing = db.query(DoctorBriefing).filter(
        DoctorBriefing.id == briefing_id,
        DoctorBriefing.user_id == current_user.id
    ).first()
    if not briefing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(briefing, k, v)

    db.commit()
    db.refresh(briefing)
    return briefing

@router.delete("/{briefing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_briefing(
    briefing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a doctor visit briefing and revokes any associated share links."""
    briefing = db.query(DoctorBriefing).filter(
        DoctorBriefing.id == briefing_id,
        DoctorBriefing.user_id == current_user.id
    ).first()
    if not briefing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found.")

    db.delete(briefing)
    db.commit()
    return None

# ==================== Secure Sharing Endpoints ====================

@router.post("/{briefing_id}/share", response_model=SharedBriefingOut, status_code=status.HTTP_201_CREATED)
def create_share_token(
    briefing_id: int,
    payload: ShareBriefingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a cryptographically secure, time-bounded share token for a specific briefing.
    Allows clinician access without exposing full account history.
    """
    briefing = db.query(DoctorBriefing).filter(
        DoctorBriefing.id == briefing_id,
        DoctorBriefing.user_id == current_user.id
    ).first()
    if not briefing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found.")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.duration_hours)

    shared = SharedBriefing(
        briefing_id=briefing.id,
        user_id=current_user.id,
        share_token=token,
        recipient_name=payload.recipient_name,
        recipient_role=payload.recipient_role,
        access_pin=payload.access_pin.strip() if payload.access_pin else None,
        expires_at=expires_at,
        is_revoked=False,
        view_count=0
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)
    return shared

@router.delete("/share/{share_token}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share_token(
    share_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revokes an active share token immediately upon user consent withdrawal.
    """
    shared = db.query(SharedBriefing).filter(
        SharedBriefing.share_token == share_token,
        SharedBriefing.user_id == current_user.id
    ).first()
    if not shared:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share token not found.")

    shared.is_revoked = True
    db.commit()
    return None

@router.get("/shared/{share_token}", response_model=PublicSharedBriefingOut)
def view_shared_briefing(
    share_token: str,
    x_access_pin: Optional[str] = Header(None, alias="X-Access-PIN"),
    pin: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Public access endpoint for a verified healthcare professional or caregiver.
    Audited, time-bounded, and read-only.
    """
    shared = db.query(SharedBriefing).filter(
        SharedBriefing.share_token == share_token
    ).first()

    if not shared:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared briefing link is invalid or expired.")

    if shared.is_revoked:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Access to this clinical briefing has been revoked by the patient.")

    # Check expiration (ensure UTC timezone comparison)
    now_utc = datetime.now(timezone.utc)
    exp = shared.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now_utc > exp:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This clinical briefing link has expired.")

    # Check optional PIN protection
    if shared.access_pin:
        provided_pin = x_access_pin or pin
        if not provided_pin or provided_pin.strip() != shared.access_pin.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This clinical briefing is protected by a security PIN. Please provide the access PIN."
            )

    # Audit access
    shared.view_count += 1
    shared.last_accessed_at = now_utc
    db.commit()

    briefing = shared.briefing
    patient_name = shared.user.name if shared.user else "Patient"

    return {
        "share_token": shared.share_token,
        "patient_name": patient_name,
        "title": briefing.title,
        "visit_reason": briefing.visit_reason,
        "symptoms_summary": briefing.symptoms_summary,
        "vitals_summary": briefing.vitals_summary,
        "allergies_summary": briefing.allergies_summary,
        "medicines_summary": briefing.medicines_summary,
        "questions_to_ask": briefing.questions_to_ask,
        "notes": briefing.notes,
        "recipient_name": shared.recipient_name,
        "expires_at": shared.expires_at,
        "is_expired": False,
        "created_at": briefing.created_at
    }
