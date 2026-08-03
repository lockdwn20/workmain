"""
Extends the ai_costs interaction_type CHECK constraint to include 'intent_parse'
for Phase 13 Sprint 1 intent parsing cost tracking.

Run once before deploying Phase 13 Sprint 1:
    python scripts/migrate_018_extend_ai_costs.py
"""

from workmain.database.connection import get_db
from sqlalchemy import text


def run_migration() -> None:
    db = get_db()
    session = db.get_session()
    try:
        session.execute(text(
            "ALTER TABLE ai_costs DROP CONSTRAINT IF EXISTS ai_costs_interaction_type_check"
        ))
        session.execute(text(
            "ALTER TABLE ai_costs ADD CONSTRAINT ai_costs_interaction_type_check "
            "CHECK (interaction_type IN ('report', 'condensation', 'intent_parse'))"
        ))
        session.commit()
        print("Migration 018 complete: ai_costs CHECK extended for 'intent_parse'")
    except Exception as e:
        session.rollback()
        print(f"Migration 018 FAILED: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
