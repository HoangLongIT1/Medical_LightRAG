"""Create the clinical_states table in PostgreSQL."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.models import Base, ClinicalState
from database.db import engine
from sqlalchemy import text

# Create table
Base.metadata.create_all(bind=engine)
print("✅ clinical_states table created")

# Verify
with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'clinical_states' ORDER BY ordinal_position"
    ))
    print("📋 Columns:")
    for row in result:
        print(f"   {row[0]}: {row[1]}")
