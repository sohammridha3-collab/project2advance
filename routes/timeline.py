"""
Health Timeline API Routes for HealthBridge AI
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User
from services.auth_handler import get_current_user
from services.context_engine import get_timeline_events
from schemas.schemas import TimelineEventOut

logger = logging.getLogger("health_risk_system")
router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("", response_model=List[TimelineEventOut])
@router.get("/", response_model=List[TimelineEventOut], include_in_schema=False)
def get_user_timeline(
    event_type: Optional[str] = Query(None, description="Filter by event type (ASSESSMENT, SYMPTOM, PRESCRIPTION, ALLERGY, BRIEFING, ALL)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns unified chronological timeline events for the authenticated patient.
    """
    try:
        events = get_timeline_events(user_id=current_user.id, event_type=event_type, db=db)
        logger.info(f"[Timeline] Successfully retrieved {len(events)} events for user #{current_user.id} (filter: {event_type or 'ALL'}).")
        return events
    except Exception as exc:
        logger.error(f"[Timeline] Unexpected error building timeline for user #{current_user.id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health continuity timeline. Please try again."
        )
