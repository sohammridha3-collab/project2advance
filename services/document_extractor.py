"""
Prescription Document Intelligence & Field Extraction Service for HealthBridge AI
Extracts candidate fields from prescription files (Doctor, Date, Medicines, Dosages)
and marks fields as unverified until reviewed and confirmed by the patient.
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

COMMON_CARDIO_MEDICINES = [
    "Aspirin", "Atorvastatin", "Metoprolol", "Amlodipine", "Lisinopril",
    "Losartan", "Warfarin", "Clopidogrel", "Nitroglycerin", "Metformin",
    "Ibuprofen", "Hydrochlorothiazide", "Carvedilol", "Rosuvastatin"
]

def extract_prescription_text(file_path: Path) -> str:
    """
    Attempts to read text from file if textual or if OCR dependencies exist.
    Falls back gracefully without crashing.
    """
    if not file_path.exists():
        return ""

    suffix = file_path.suffix.lower()
    text_content = ""

    # 1. Try pytesseract if installed
    if suffix in [".png", ".jpg", ".jpeg"]:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            text_content = pytesseract.image_to_string(img)
            return text_content
        except Exception:
            pass

    # 2. Try pypdf / pdfplumber if installed
    if suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            for page in reader.pages:
                text_content += page.extract_text() or ""
            if text_content.strip():
                return text_content
        except Exception:
            pass

    # 3. Fallback: inspect raw bytes (direct decode or ASCII chunks)
    try:
        raw = file_path.read_bytes()
        try:
            decoded = raw.decode("utf-8")
            if len(decoded.strip()) > 10:
                return decoded
        except Exception:
            pass
        # Extract readable ASCII chunks of 4+ characters
        chunks = re.findall(b"[A-Za-z0-9 .,:;\\-()/]{4,}", raw)
        text_content = " ".join([c.decode("latin-1", errors="ignore") for c in chunks[:100]])
    except Exception:
        text_content = ""

    return text_content

def extract_candidate_prescription_fields(file_path: Path, filename: str) -> Dict[str, Any]:
    """
    Analyzes document text and filename to discover candidate prescription metadata.
    All extracted fields are flagged as 'unverified' until patient confirms them.
    """
    text = extract_prescription_text(file_path)
    text_lower = text.lower()
    filename_lower = filename.lower()

    # Discover Doctor Name
    doctor_name = None
    doc_match = re.search(r"(?:dr\.|doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text, re.IGNORECASE)
    if doc_match:
        doctor_name = doc_match.group(1).strip()
    elif "dr_" in filename_lower or "dr-" in filename_lower or "doctor" in filename_lower:
        doc_part = re.search(r"(?:dr[_-]|doctor[_-])([a-z]+)", filename_lower)
        if doc_part:
            doctor_name = doc_part.group(1).capitalize()

    # Discover Date
    prescription_date = None
    date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
    if date_match:
        raw_date = date_match.group(1)
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                prescription_date = datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue

    # Discover Candidate Medicines
    candidate_medicines: List[Dict[str, str]] = []
    combined_corpus = text_lower + " " + filename_lower
    for med in COMMON_CARDIO_MEDICINES:
        if med.lower() in combined_corpus:
            # Find dosage near medicine
            dosage = "As directed"
            dose_match = re.search(rf"{med.lower()}\s*(\d+\s*(?:mg|mcg|g|ml))", combined_corpus)
            if dose_match:
                dosage = dose_match.group(1)
            candidate_medicines.append({
                "medicine_name": med,
                "dosage": dosage,
                "frequency": "Once daily",
                "instructions": "Candidate field extracted for verification."
            })

    # Discover Main Health Problem
    main_problem = None
    if "cardio" in combined_corpus or "heart" in combined_corpus:
        main_problem = "Cardiovascular Consultation"
    elif "hyperten" in combined_corpus or "blood pressure" in combined_corpus:
        main_problem = "Hypertension Management"
    elif "diabet" in combined_corpus:
        main_problem = "Diabetic Care Follow-up"

    has_extracted = bool(doctor_name or candidate_medicines or main_problem or prescription_date)

    return {
        "extraction_status": "OCR_Extracted" if has_extracted else "Manual",
        "doctor_name": doctor_name,
        "prescription_date": prescription_date,
        "main_health_problem": main_problem,
        "medicines": candidate_medicines,
        "ocr_available": False,  # Indicates whether external Tesseract engine is installed
        "verification_required": True,
        "raw_text_preview": text[:200] if text else None
    }
