import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("uvicorn")

from sqlalchemy import event, text

raw_database_url = os.getenv("DATABASE_URL", "sqlite:///./health_risk.db")

# PostgreSQL compatibility fix for SQLAlchemy (postgres:// -> postgresql://)
if raw_database_url.startswith("postgres://"):
    raw_database_url = raw_database_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if raw_database_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30.0  # 30-second busy timeout prevents "database is locked"
    }
    engine_kwargs["connect_args"] = connect_args
elif "postgresql" in raw_database_url:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20
    })

try:
    engine = create_engine(raw_database_url, **engine_kwargs)
    with engine.connect() as conn:
        pass
except Exception as exc:
    # If PostgreSQL connection fails in local development environment, fallback gracefully to SQLite
    if "postgresql" in raw_database_url:
        logger.warning(
            f"Could not connect to PostgreSQL ({exc}). Falling back to SQLite for local development."
        )
        raw_database_url = "sqlite:///./health_risk.db"
        engine = create_engine(
            raw_database_url,
            connect_args={"check_same_thread": False, "timeout": 30.0},
            pool_pre_ping=True
        )
    else:
        raise exc

# Configure SQLite for high concurrency (WAL mode allows concurrent readers and writers)
if raw_database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA busy_timeout = 30000")
            cursor.close()
        except Exception as pragma_err:
            logger.warning(f"[Database] Could not configure SQLite PRAGMAs: {pragma_err}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables and seed default medicine, interaction, and demo data."""
    from . import models
    Base.metadata.create_all(bind=engine)
    migrate_prescription_schema()
    migrate_assessment_schema()
    migrate_healthbridge_schema()
    seed_reference_medicines()
    seed_demo_user()

def migrate_healthbridge_schema():
    """Safely adds missing HealthBridge AI columns and tables to existing database."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        with engine.connect() as conn:
            # 1. recent_problems: status, notes
            if "recent_problems" in table_names:
                prob_cols = [c["name"] for c in inspector.get_columns("recent_problems")]
                if "status" not in prob_cols:
                    try:
                        conn.execute(text("ALTER TABLE recent_problems ADD COLUMN status VARCHAR(50) DEFAULT 'Active'"))
                        conn.commit()
                        logger.info("[Database] Migrated recent_problems: added status column.")
                    except Exception as e:
                        logger.warning(f"RecentProblem status migration note: {e}")
                if "notes" not in prob_cols:
                    try:
                        conn.execute(text("ALTER TABLE recent_problems ADD COLUMN notes TEXT"))
                        conn.commit()
                        logger.info("[Database] Migrated recent_problems: added notes column.")
                    except Exception as e:
                        logger.warning(f"RecentProblem notes migration note: {e}")

            # 2. allergies: verification_status, created_at
            if "allergies" in table_names:
                allg_cols = [c["name"] for c in inspector.get_columns("allergies")]
                if "verification_status" not in allg_cols:
                    try:
                        conn.execute(text("ALTER TABLE allergies ADD COLUMN verification_status VARCHAR(50) DEFAULT 'Self-Reported'"))
                        conn.commit()
                        logger.info("[Database] Migrated allergies: added verification_status column.")
                    except Exception as e:
                        logger.warning(f"Allergy verification_status migration note: {e}")
                if "created_at" not in allg_cols:
                    try:
                        conn.execute(text("ALTER TABLE allergies ADD COLUMN created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)"))
                        conn.commit()
                        logger.info("[Database] Migrated allergies: added created_at column.")
                    except Exception as e:
                        try:
                            conn.execute(text("ALTER TABLE allergies ADD COLUMN created_at DATETIME"))
                            conn.commit()
                            logger.info("[Database] Migrated allergies: added created_at column (nullable).")
                        except Exception as e2:
                            logger.warning(f"Allergy created_at migration note: {e2}")

            # 3. prescriptions: extraction_status
            if "prescriptions" in table_names:
                rx_cols = [c["name"] for c in inspector.get_columns("prescriptions")]
                if "extraction_status" not in rx_cols:
                    try:
                        conn.execute(text("ALTER TABLE prescriptions ADD COLUMN extraction_status VARCHAR(50) DEFAULT 'Manual'"))
                        conn.commit()
                        logger.info("[Database] Migrated prescriptions: added extraction_status column.")
                    except Exception as e:
                        logger.warning(f"Prescription extraction_status migration note: {e}")
                if "title" not in rx_cols:
                    try:
                        conn.execute(text("ALTER TABLE prescriptions ADD COLUMN title VARCHAR(200)"))
                        conn.commit()
                        logger.info("[Database] Migrated prescriptions: added title column.")
                    except Exception as e:
                        logger.warning(f"Prescription title migration note: {e}")
    except Exception as exc:
        logger.warning(f"HealthBridge schema migration check note: {exc}")

def migrate_assessment_schema():
    """Safely adds the nullable probabilities_json column to health_assessments on existing DBs."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "health_assessments" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("health_assessments")]
            if "probabilities_json" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE health_assessments ADD COLUMN probabilities_json TEXT"))
                    conn.commit()
                    logger.info("[Database] Migrated health_assessments: added probabilities_json column.")
    except Exception as exc:
        logger.warning(f"Assessment schema migration note: {exc}")

def migrate_prescription_schema():
    """Safely adds missing columns to prescriptions table if upgrading an existing DB."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "prescriptions" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("prescriptions")]
            with engine.connect() as conn:
                if "main_health_problem" not in columns:
                    try:
                        conn.execute(text("ALTER TABLE prescriptions ADD COLUMN main_health_problem VARCHAR(200)"))
                        conn.commit()
                        logger.info("[Database] Migrated prescriptions: added main_health_problem column.")
                    except Exception as e:
                        logger.warning(f"Migration note (main_health_problem): {e}")
                if "original_filename" not in columns:
                    try:
                        conn.execute(text("ALTER TABLE prescriptions ADD COLUMN original_filename VARCHAR(255)"))
                        conn.commit()
                        logger.info("[Database] Migrated prescriptions: added original_filename column.")
                    except Exception as e:
                        logger.warning(f"Migration note (original_filename): {e}")
                if "updated_at" not in columns:
                    try:
                        conn.execute(text("ALTER TABLE prescriptions ADD COLUMN updated_at DATETIME"))
                        conn.commit()
                        logger.info("[Database] Migrated prescriptions: added updated_at column.")
                    except Exception as e:
                        logger.warning(f"Migration note (updated_at): {e}")
    except Exception as exc:
        logger.warning(f"Schema migration check note: {exc}")

def seed_demo_user():
    """Seeds a ready-to-use demo patient account for testing."""
    from . import models
    from services.auth_handler import get_password_hash
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == "demo@health.io").first()
        if not user:
            demo_user = models.User(
                name="Demo Patient",
                email="demo@health.io",
                password_hash=get_password_hash("Demo123!")
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            profile = models.HealthProfile(
                user_id=demo_user.id,
                age=45,
                gender="Male",
                smoker_status="No",
                diabetes_history="No"
            )
            db.add(profile)
            db.commit()
    except Exception as e:
        logger.warning(f"Error seeding demo user: {e}")
        db.rollback()
    finally:
        db.close()

def seed_reference_medicines():
    """Seeds reference medicines and interactions for the safety layer if not already populated."""
    from . import models
    db = SessionLocal()
    try:
        if db.query(models.Medicine).count() == 0:
            sample_medicines = [
                models.Medicine(
                    medicine_name="Aspirin",
                    generic_name="Acetylsalicylic Acid",
                    category="Antiplatelet / NSAID",
                    common_uses="Cardiovascular event prevention, pain relief",
                    contraindications="Peptic ulcer, active bleeding, hemophilia",
                    warnings="Risk of gastrointestinal bleeding; caution in patients with asthma.",
                    prescription_required=False
                ),
                models.Medicine(
                    medicine_name="Ibuprofen",
                    generic_name="Ibuprofen",
                    category="NSAID",
                    common_uses="Pain relief, inflammation reduction",
                    contraindications="Kidney disease, active gastrointestinal bleed, severe heart failure",
                    warnings="May blunt cardioprotective effect of aspirin and elevate blood pressure.",
                    prescription_required=False
                ),
                models.Medicine(
                    medicine_name="Metoprolol",
                    generic_name="Metoprolol Tartrate / Succinate",
                    category="Beta Blocker",
                    common_uses="Hypertension, angina, heart failure management",
                    contraindications="Severe bradycardia, second- or third-degree heart block, cardiogenic shock",
                    warnings="Do not discontinue abruptly. Monitor resting heart rate and blood pressure.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Amlodipine",
                    generic_name="Amlodipine Besylate",
                    category="Calcium Channel Blocker",
                    common_uses="Hypertension, coronary artery disease",
                    contraindications="Severe hypotension, cardiogenic shock",
                    warnings="May cause peripheral edema and dizziness.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Lisinopril",
                    generic_name="Lisinopril",
                    category="ACE Inhibitor",
                    common_uses="Hypertension, heart failure, post-myocardial infarction",
                    contraindications="History of angioedema, pregnancy",
                    warnings="Risk of hyperkalemia and renal impairment. Monitor serum potassium.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Atorvastatin",
                    generic_name="Atorvastatin Calcium",
                    category="Statin / HMG-CoA Reductase Inhibitor",
                    common_uses="Hypercholesterolemia, cardiovascular risk reduction",
                    contraindications="Active liver disease, pregnancy",
                    warnings="Report unexplained muscle aches or weakness (risk of rhabdomyolysis).",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Warfarin",
                    generic_name="Warfarin Sodium",
                    category="Anticoagulant",
                    common_uses="Prevention of thromboembolism, atrial fibrillation",
                    contraindications="Active bleeding, severe hepatic disease, pregnancy",
                    warnings="Narrow therapeutic index. Requires INR monitoring; high interaction risk.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Nitroglycerin",
                    generic_name="Nitroglycerin",
                    category="Nitrate / Vasodilator",
                    common_uses="Acute angina relief and prevention",
                    contraindications="Concurrent use with PDE-5 inhibitors (e.g. Sildenafil), severe anemia",
                    warnings="May cause marked hypotension and reflexive tachycardia.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Metformin",
                    generic_name="Metformin Hydrochloride",
                    category="Biguanide / Antidiabetic",
                    common_uses="Type 2 diabetes glycemic control, metabolic health",
                    contraindications="Severe renal impairment (eGFR < 30), metabolic acidosis, acute heart failure",
                    warnings="Risk of lactic acidosis; hold before radiographic iodinated contrast procedures.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Losartan",
                    generic_name="Losartan Potassium",
                    category="Angiotensin II Receptor Blocker (ARB)",
                    common_uses="Hypertension, diabetic nephropathy, stroke risk reduction",
                    contraindications="Pregnancy, concurrent use with aliskiren in patients with diabetes",
                    warnings="Risk of hyperkalemia and renal function decline. Monitor serum creatinine and potassium.",
                    prescription_required=True
                ),
                models.Medicine(
                    medicine_name="Clopidogrel",
                    generic_name="Clopidogrel Bisulfate",
                    category="Antiplatelet / P2Y12 Inhibitor",
                    common_uses="Atherothrombotic event prevention, myocardial infarction, stroke",
                    contraindications="Active pathological bleeding (e.g., peptic ulcer, intracranial hemorrhage)",
                    warnings="Significant bleeding risk; consult physician before elective surgery or when combining with NSAIDs.",
                    prescription_required=True
                )
            ]
            db.add_all(sample_medicines)
            db.commit()

        if db.query(models.MedicineInteraction).count() == 0:
            sample_interactions = [
                models.MedicineInteraction(
                    medicine_a="Aspirin",
                    medicine_b="Ibuprofen",
                    interaction_level="Moderate",
                    description="Ibuprofen may interfere with the antiplatelet effect of low-dose aspirin and increase bleeding risk."
                ),
                models.MedicineInteraction(
                    medicine_a="Aspirin",
                    medicine_b="Warfarin",
                    interaction_level="High",
                    description="Synergistic antithrombotic effect greatly elevates risk of major gastrointestinal and systemic bleeding."
                ),
                models.MedicineInteraction(
                    medicine_a="Aspirin",
                    medicine_b="Clopidogrel",
                    interaction_level="Moderate",
                    description="Dual antiplatelet therapy increases systemic bleeding risk; requires clinician oversight."
                ),
                models.MedicineInteraction(
                    medicine_a="Metoprolol",
                    medicine_b="Amlodipine",
                    interaction_level="Minor",
                    description="Additive blood pressure reduction; potential risk of symptomatic bradycardia."
                ),
                models.MedicineInteraction(
                    medicine_a="Lisinopril",
                    medicine_b="Ibuprofen",
                    interaction_level="Moderate",
                    description="NSAIDs can diminish the antihypertensive effect of ACE inhibitors and worsen renal function."
                ),
                models.MedicineInteraction(
                    medicine_a="Lisinopril",
                    medicine_b="Losartan",
                    interaction_level="High",
                    description="Dual renin-angiotensin-aldosterone blockade increases risks of hypotension, hyperkalemia, and acute renal impairment."
                ),
                models.MedicineInteraction(
                    medicine_a="Warfarin",
                    medicine_b="Ibuprofen",
                    interaction_level="High",
                    description="Severe risk of upper gastrointestinal ulceration and hemorrhage."
                ),
                models.MedicineInteraction(
                    medicine_a="Nitroglycerin",
                    medicine_b="Sildenafil",
                    interaction_level="Critical",
                    description="Concomitant administration causes severe, potentially fatal hypotensive collapse."
                )
            ]
            db.add_all(sample_interactions)
            db.commit()
    except Exception as e:
        logger.error(f"Error seeding medicine reference data: {e}")
        db.rollback()
    finally:
        db.close()

