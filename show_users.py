"""
Command-line utility to display all registered users saved in health_risk.db
Usage: python show_users.py
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def show_registered_users():
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "health_risk.db"

    print("=" * 80)
    print(" AI HEALTH RISK PREDICTION SYSTEM - REGISTERED ACCOUNTS VIEWER")
    print("=" * 80)
    print(f"Database File: {db_path.resolve()}")
    print(f"File Exists:   {db_path.exists()} (Size: {db_path.stat().st_size if db_path.exists() else 0:,} bytes)")
    print(f"Database Table: users")
    print("=" * 80)

    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}.")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.created_at,
                   COUNT(a.id) as assessments_count
            FROM users u
            LEFT JOIN health_assessments a ON a.user_id = u.id
            GROUP BY u.id
            ORDER BY u.id ASC
        """)
        rows = cursor.fetchall()

        if not rows:
            print("No registered users found in the database.")
            return

        print(f"Total Registered Users: {len(rows)}\n")
        header = f"{'ID':<6} | {'Full Name':<22} | {'Email Address':<32} | {'Registered Date':<19} | {'Assessments'}"
        print(header)
        print("-" * len(header))

        for r in rows:
            uid, name, email, created_at, asmt_count = r
            dt_str = str(created_at)[:19] if created_at else "N/A"
            print(f"{uid:<6} | {name:<22} | {email:<32} | {dt_str:<19} | {asmt_count}")

        print("-" * len(header))
        print(f"\n[Security Notice] Passwords are encrypted using bcrypt (Blowfish) in the 'password_hash' column.")
        print("[Client Token] When logged in, your signed JWT token is stored in the browser's localStorage ('hr_auth_token').")
        print("=" * 80)

    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_registered_users()
