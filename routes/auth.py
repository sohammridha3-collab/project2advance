from datetime import timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from schemas.schemas import (
    UserCreate, UserLogin, UserOut, Token, UserProfileOut, UserProfileUpdate
)
from database.database import get_db
from database.models import User, HealthProfile, LoginActivity
from services.auth_handler import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user and creates an initial health profile."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_pw
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Automatically create user's initial empty health profile
    profile = HealthProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)

    # Record registration in login_activities
    try:
        db.add(LoginActivity(
            user_id=user.id,
            email=user.email,
            name=user.name,
            activity_type="REGISTER",
            status="SUCCESS"
        ))
        db.commit()
    except Exception:
        pass

    return user

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticates a user via OAuth2 form or JSON payload and returns a signed JWT access token.
    Supports both Swagger UI form-data and JSON clients.
    """
    username = None
    password = None

    # Try JSON body first
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            pass

    # Fallback to form data
    if not username:
        try:
            form = await request.form()
            username = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required."
        )

    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.password_hash):
        try:
            db.add(LoginActivity(email=username, activity_type="LOGIN", status="FAILED"))
            db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record successful login
    try:
        db.add(LoginActivity(
            user_id=user.id,
            email=user.email,
            name=user.name,
            activity_type="LOGIN",
            status="SUCCESS"
        ))
        db.commit()
    except Exception:
        pass

    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=token_expires
    )

    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Returns the authenticated user's details and health profile."""
    return user

@router.put("/me/profile", response_model=UserProfileOut)
def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Updates the authenticated user's personal health profile."""
    profile = user.profile
    if not profile:
        profile = HealthProfile(user_id=user.id)
        db.add(profile)

    if profile_data.age is not None:
        profile.age = profile_data.age
    if profile_data.gender is not None:
        profile.gender = profile_data.gender
    if profile_data.smoker_status is not None:
        profile.smoker_status = profile_data.smoker_status
    if profile_data.diabetes_history is not None:
        profile.diabetes_history = profile_data.diabetes_history

    db.commit()
    db.refresh(profile)
    return profile

@router.get("/users", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    """Returns a list of all registered users (for verification and demonstration)."""
    return db.query(User).order_by(User.created_at.desc()).all()

@router.get("/admin/logins")
def get_login_history(db: Session = Depends(get_db)):
    """Returns the login and registration activity history for admin view."""
    records = db.query(LoginActivity).order_by(LoginActivity.timestamp.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "email": r.email,
            "name": r.name,
            "activity_type": r.activity_type,
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None
        }
        for r in records
    ]

