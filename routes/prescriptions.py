import os
import re
import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import (
    APIRouter, Depends, HTTPException, status, Request, UploadFile, File
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from schemas.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionOut,
    PrescriptionMedicineCreate,
    PrescriptionMedicineUpdate,
    PrescriptionMedicineOut,
)
from database.database import get_db
from database.models import Prescription, PrescriptionMedicine, User
from services.auth_handler import get_current_user, get_optional_current_user
from services.document_extractor import extract_candidate_prescription_fields

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

# Base upload directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIRECTORY", str(Path(__file__).resolve().parent.parent / "uploads" / "prescriptions")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Security constraints
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png"
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def sanitize_filename(filename: str) -> str:
    """Removes path traversal characters and illegal characters."""
    base = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base)
    return clean_name


# ============================================================
# 1. LIST PRESCRIPTIONS
# ============================================================
@router.get("", response_model=List[PrescriptionOut], include_in_schema=False)
@router.get("/", response_model=List[PrescriptionOut])
def get_user_prescriptions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieves all medical prescriptions for the authenticated user, sorted newest first."""
    return (
        db.query(Prescription)
        .filter(Prescription.user_id == user.id)
        .order_by(Prescription.prescription_date.desc(), Prescription.created_at.desc())
        .all()
    )


# ============================================================
# 2. CREATE PRESCRIPTION (Supports Multipart Upload & JSON Body)
# ============================================================
async def _process_prescription_creation(
    request: Request,
    db: Session,
    user: User
) -> Prescription:
    content_type = request.headers.get("content-type", "").lower()
    
    saved_rel_path: Optional[str] = None
    orig_filename: Optional[str] = None
    title: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    main_health_problem: Optional[str] = None
    prescription_date_str: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    medicines_to_add: List[dict] = []
    extraction_status_val: Optional[str] = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")

        if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
            ext = Path(uploaded_file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file extension '{ext}'. Only PDF, JPG, JPEG, and PNG are allowed."
                )

            if uploaded_file.content_type and uploaded_file.content_type.lower() not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content type '{uploaded_file.content_type}'. Upload only PDF documents or images."
                )

            contents = await uploaded_file.read()
            if len(contents) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
                )

            orig_filename = sanitize_filename(uploaded_file.filename)
            unique_filename = f"{uuid.uuid4().hex[:12]}_{orig_filename}"
            destination = UPLOAD_DIR / unique_filename

            if not destination.resolve().is_relative_to(UPLOAD_DIR.resolve()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security error: Invalid file path."
                )

            with open(destination, "wb") as f:
                f.write(contents)

            saved_rel_path = unique_filename

        title = form.get("title")
        doctor_name = form.get("doctor_name")
        hospital_name = form.get("hospital_name")
        main_health_problem = form.get("main_health_problem")
        prescription_date_str = form.get("prescription_date")
        diagnosis = form.get("diagnosis")
        notes = form.get("notes")
        extraction_status_val = form.get("extraction_status")

        raw_meds = form.get("medicines")
        if raw_meds:
            try:
                parsed_meds = json.loads(raw_meds) if isinstance(raw_meds, str) else raw_meds
                if isinstance(parsed_meds, list):
                    medicines_to_add = parsed_meds
            except Exception:
                pass

    else:
        # JSON body
        try:
            body = await request.json()
        except Exception:
            body = {}
        
        title = body.get("title")
        doctor_name = body.get("doctor_name")
        hospital_name = body.get("hospital_name")
        main_health_problem = body.get("main_health_problem")
        prescription_date_str = body.get("prescription_date")
        diagnosis = body.get("diagnosis")
        notes = body.get("notes")
        saved_rel_path = body.get("file_path")
        orig_filename = body.get("original_filename")
        medicines_to_add = body.get("medicines", [])
        extraction_status_val = body.get("extraction_status")

    # Parse date
    dt_val: Optional[datetime] = None
    if prescription_date_str:
        if isinstance(prescription_date_str, datetime):
            dt_val = prescription_date_str
        else:
            try:
                dt_val = datetime.fromisoformat(str(prescription_date_str).replace("Z", "+00:00"))
            except Exception:
                try:
                    dt_val = datetime.strptime(str(prescription_date_str)[:10], "%Y-%m-%d")
                except Exception:
                    dt_val = datetime.now()

    new_prescription = Prescription(
        user_id=user.id,
        title=str(title).strip() if title else None,
        doctor_name=str(doctor_name).strip() if doctor_name else None,
        hospital_name=str(hospital_name).strip() if hospital_name else None,
        main_health_problem=str(main_health_problem).strip() if main_health_problem else None,
        prescription_date=dt_val,
        diagnosis=str(diagnosis).strip() if diagnosis else None,
        notes=str(notes).strip() if notes else None,
        file_path=saved_rel_path,
        original_filename=orig_filename,
        extraction_status=str(extraction_status_val or ("OCR_Extracted" if saved_rel_path else "Manual"))
    )
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    # Attach medicines
    for item in medicines_to_add:
        if isinstance(item, dict) and item.get("medicine_name"):
            med_name = str(item.get("medicine_name") or "").strip()
            if med_name:
                pm = PrescriptionMedicine(
                    prescription_id=new_prescription.id,
                    medicine_name=med_name,
                    dosage=str(item.get("dosage") or "").strip() or None,
                    frequency=str(item.get("frequency") or "").strip() or None,
                    duration=str(item.get("duration") or "").strip() or None,
                    instructions=str(item.get("instructions") or "").strip() or None
                )
                db.add(pm)
    
    db.commit()
    db.refresh(new_prescription)
    return new_prescription


@router.post("", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Creates a prescription from multipart upload (with file) or JSON body."""
    return await _process_prescription_creation(request, db, user)


@router.post("/upload", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def upload_prescription_alias(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Compatibility alias for multipart prescription uploads."""
    return await _process_prescription_creation(request, db, user)


@router.post("/extract")
async def extract_prescription_fields_endpoint(
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Analyzes an uploaded prescription file and extracts candidate fields
    (Doctor, Date, Medicines, Dosages) for patient review before saving.
    """
    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" not in content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected multipart/form-data with file.")

    form = await request.form()
    upload = form.get("file")
    if not upload or not hasattr(upload, "filename"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No prescription file uploaded.")

    filename = sanitize_filename(upload.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File extension {suffix} is not allowed.")

    file_bytes = await upload.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit.")

    unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    disk_path = UPLOAD_DIR / unique_name
    disk_path.write_bytes(file_bytes)

    extracted = extract_candidate_prescription_fields(disk_path, filename)
    extracted["staged_file_path"] = f"uploads/prescriptions/{unique_name}"
    extracted["original_filename"] = filename
    return {
        "status": "extracted",
        "extracted_data": extracted,
        **extracted,
        "notice": "Candidate details extracted by AI. Please review and verify all dosages and medicines before saving."
    }


# ============================================================
# 3. GET SINGLE PRESCRIPTION
# ============================================================
@router.get("/{prescription_id}", response_model=PrescriptionOut)
def get_prescription_by_id(
    prescription_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieves a single prescription record by ID for the authenticated user."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or access denied."
        )

    return prescription


# ============================================================
# 4. UPDATE PRESCRIPTION INFORMATION
# ============================================================
@router.put("/{prescription_id}", response_model=PrescriptionOut)
def update_prescription(
    prescription_id: int,
    update_in: PrescriptionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Updates structured clinical fields for an existing prescription."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or access denied."
        )

    if update_in.title is not None:
        prescription.title = update_in.title.strip() if update_in.title else None
    if update_in.main_health_problem is not None:
        prescription.main_health_problem = update_in.main_health_problem.strip() if update_in.main_health_problem else None
    if update_in.doctor_name is not None:
        prescription.doctor_name = update_in.doctor_name.strip() if update_in.doctor_name else None
    if update_in.hospital_name is not None:
        prescription.hospital_name = update_in.hospital_name.strip() if update_in.hospital_name else None
    if update_in.prescription_date is not None:
        prescription.prescription_date = update_in.prescription_date
    if update_in.diagnosis is not None:
        prescription.diagnosis = update_in.diagnosis.strip() if update_in.diagnosis else None
    if update_in.notes is not None:
        prescription.notes = update_in.notes.strip() if update_in.notes else None

    prescription.updated_at = datetime.now()
    db.commit()
    db.refresh(prescription)
    return prescription


# ============================================================
# 5. DELETE PRESCRIPTION & ASSOCIATED FILE SAFELY
# ============================================================
@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Deletes a prescription record and any attached file owned by the authenticated user."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or access denied."
        )

    # Delete physical file if exists
    if prescription.file_path:
        file_path = (UPLOAD_DIR / prescription.file_path).resolve()
        if file_path.exists() and file_path.is_relative_to(UPLOAD_DIR.resolve()):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"[Prescriptions] Warning: Could not remove file {file_path}: {e}")

    db.delete(prescription)
    db.commit()
    return None


# ============================================================
# 6. MEDICINES SUB-RESOURCE ENDPOINTS
# ============================================================
@router.post("/{prescription_id}/medicines", response_model=PrescriptionMedicineOut, status_code=status.HTTP_201_CREATED)
def add_prescription_medicine(
    prescription_id: int,
    med_in: PrescriptionMedicineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Adds a medicine record to an existing prescription."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or access denied."
        )

    if not med_in.medicine_name or not med_in.medicine_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Medicine name is required."
        )

    new_med = PrescriptionMedicine(
        prescription_id=prescription.id,
        medicine_name=med_in.medicine_name.strip(),
        dosage=med_in.dosage.strip() if med_in.dosage else None,
        frequency=med_in.frequency.strip() if med_in.frequency else None,
        duration=med_in.duration.strip() if med_in.duration else None,
        instructions=med_in.instructions.strip() if med_in.instructions else None
    )
    db.add(new_med)
    prescription.updated_at = datetime.now()
    db.commit()
    db.refresh(new_med)
    return new_med


@router.put("/{prescription_id}/medicines/{medicine_id}", response_model=PrescriptionMedicineOut)
def update_prescription_medicine(
    prescription_id: int,
    medicine_id: int,
    med_in: PrescriptionMedicineUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Updates a medicine record within a prescription."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or access denied."
        )

    med = db.query(PrescriptionMedicine).filter(
        PrescriptionMedicine.id == medicine_id,
        PrescriptionMedicine.prescription_id == prescription_id
    ).first()

    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine record not found in this prescription."
        )

    if med_in.medicine_name is not None:
        clean_name = med_in.medicine_name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Medicine name cannot be empty."
            )
        med.medicine_name = clean_name

    if med_in.dosage is not None:
        med.dosage = med_in.dosage.strip() if med_in.dosage else None
    if med_in.frequency is not None:
        med.frequency = med_in.frequency.strip() if med_in.frequency else None
    if med_in.duration is not None:
        med.duration = med_in.duration.strip() if med_in.duration else None
    if med_in.instructions is not None:
        med.instructions = med_in.instructions.strip() if med_in.instructions else None

    prescription.updated_at = datetime.now()
    db.commit()
    db.refresh(med)
    return med


@router.delete("/{prescription_id}/medicines/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription_medicine(
    prescription_id: int,
    medicine_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Deletes a medicine record from an existing prescription."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or access denied."
        )

    med = db.query(PrescriptionMedicine).filter(
        PrescriptionMedicine.id == medicine_id,
        PrescriptionMedicine.prescription_id == prescription_id
    ).first()

    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine record not found in this prescription."
        )

    db.delete(med)
    prescription.updated_at = datetime.now()
    db.commit()
    return None


# ============================================================
# 7. SECURE PRESCRIPTION FILE RETRIEVAL
# ============================================================
@router.get("/{prescription_id}/file")
def download_prescription_file(
    prescription_id: int,
    token: Optional[str] = None,
    download: bool = False,
    db: Session = Depends(get_db),
    auth_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Secure file retrieval:
    Ensures prescription belongs to current authenticated user (via Authorization header or query token),
    then securely serves the prescription document. Supports inline preview and direct download attachment.
    """
    user = auth_user
    if not user and token:
        from jose import jwt, JWTError
        from services.auth_handler import SECRET_KEY, ALGORITHM
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email = payload.get("sub")
            if user_email:
                user = db.query(User).filter(User.email == user_email).first()
        except Exception:
            pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view prescription documents."
        )

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.user_id == user.id
    ).first()

    if not prescription or not prescription.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription document not found or access denied."
        )

    file_path = (UPLOAD_DIR / prescription.file_path).resolve()
    if not file_path.exists() or not file_path.is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File could not be found on server storage."
        )

    ext = file_path.suffix.lower()
    if ext == ".pdf":
        media_type = "application/pdf"
    elif ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif ext == ".png":
        media_type = "image/png"
    else:
        media_type = "application/octet-stream"

    filename = prescription.original_filename or file_path.name
    disposition_type = "attachment" if download else "inline"
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        content_disposition_type=disposition_type
    )

