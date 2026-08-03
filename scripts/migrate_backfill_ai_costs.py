"""
Backfill-only script. Reads all reports rows that contain cost data in
report_metadata and inserts corresponding ai_costs rows.

Run AFTER applying migration 017_ai_costs.sql:
    psql -U workmain_user -d workmain -f workmain/database/migrations/017_ai_costs.sql
    python scripts/migrate_backfill_ai_costs.py

Idempotent — reports that already have a matching ai_costs row are skipped.
"""

import sys

from sqlalchemy import text

from workmain.database.connection import get_db


def main():
    db = get_db()
    session = db.get_session()
    try:
        # Verify 017 migration has been applied
        result = session.execute(text(
            "SELECT to_regclass('public.ai_costs')"
        )).scalar()
        if result is None:
            print("ERROR: ai_costs table does not exist.")
            print("Apply migration 017_ai_costs.sql first:")
            print("  psql -U workmain_user -d workmain -f workmain/database/migrations/017_ai_costs.sql")
            sys.exit(1)

        # Fetch all reports with cost data in metadata
        # Note: ORM attribute is report_metadata; DB column is 'metadata'
        rows = session.execute(text("""
            SELECT id, report_type, metadata
            FROM reports
            WHERE metadata IS NOT NULL
              AND metadata != 'null'::jsonb
              AND (metadata->>'cost') IS NOT NULL
        """)).fetchall()

        inserted = 0
        skipped = 0

        for row in rows:
            report_id = row[0]
            report_type = row[1]
            metadata = row[2]

            # Skip if already backfilled
            existing = session.execute(text("""
                SELECT id FROM ai_costs
                WHERE report_id = :report_id
                  AND interaction_type = 'report'
                LIMIT 1
            """), {'report_id': report_id}).fetchone()

            if existing:
                skipped += 1
                continue

            provider = metadata.get('ai_provider', 'unknown')
            model = metadata.get('model')
            prompt_tokens = int(metadata.get('prompt_tokens', 0))
            completion_tokens = int(metadata.get('completion_tokens', 0))
            total_tokens = int(metadata.get('total_tokens', prompt_tokens + completion_tokens))
            cost_usd = float(metadata.get('cost', 0))
            generation_time_s = metadata.get('generation_time_s')

            session.execute(text("""
                INSERT INTO ai_costs (
                    interaction_type, provider, model,
                    prompt_tokens, completion_tokens, total_tokens,
                    cost_usd, generation_time_s,
                    report_id, context_label
                ) VALUES (
                    'report', :provider, :model,
                    :prompt_tokens, :completion_tokens, :total_tokens,
                    :cost_usd, :generation_time_s,
                    :report_id, :context_label
                )
            """), {
                'provider': provider,
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost_usd,
                'generation_time_s': generation_time_s,
                'report_id': report_id,
                'context_label': report_type,
            })
            inserted += 1

        session.commit()
        print(f"Backfill complete: {inserted} rows inserted, {skipped} rows skipped.")

    finally:
        session.close()


if __name__ == '__main__':
    main()
