"""
Health Timeline API Routes for HealthBridge AI
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User
from services.auth_handler import get_current_user
from services.context_engine import get_timeline_events
from schemas.schemas import TimelineEventOut

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("", response_model=List[TimelineEventOut])
def get_user_timeline(
    event_type: Optional[str] = Query(None, description="Filter by event type (ASSESSMENT, SYMPTOM, PRESCRIPTION, ALLERGY, BRIEFING, ALL)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns unified chronological timeline events for the authenticated patient.
    """
    return get_timeline_events(user_id=current_user.id, event_type=event_type, db=db)
