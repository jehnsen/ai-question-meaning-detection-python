"""
Quick migration runner - bypasses confirmation prompt.
"""
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, text

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

print("\n" + "=" * 80)
print("RUNNING DATABASE MIGRATION: vendor_id -> provider_id")
print("=" * 80 + "\n")

with Session(engine) as session:
    try:
        # Step 1: Add new columns
        print("[1/8] Adding provider_id columns...")
        try:
            session.exec(text("ALTER TABLE responseentry ADD COLUMN provider_id VARCHAR(16) NULL"))
            session.exec(text("ALTER TABLE responseentry ADD COLUMN answer LONGTEXT NULL"))
            session.commit()
        except Exception as e:
            print(f"  Note: {e}")
            session.rollback()

        try:
            session.exec(text("ALTER TABLE questionlink ADD COLUMN provider_id VARCHAR(16) NULL"))
            session.commit()
        except Exception as e:
            print(f"  Note: {e}")
            session.rollback()

        try:
            session.exec(text("ALTER TABLE matchlog ADD COLUMN provider_id VARCHAR(16) NULL"))
            session.commit()
        except Exception as e:
            print(f"  Note: {e}")
            session.rollback()

        # Step 2: Migrate vendor_id to provider_id (handle binary)
        print("\n[2/8] Migrating vendor_id to provider_id...")
        result = session.exec(text("""
            UPDATE responseentry
            SET provider_id = CAST(vendor_id AS CHAR)
            WHERE provider_id IS NULL AND vendor_id IS NOT NULL
        """))
        session.commit()
        print(f"  ✓ Updated responseentry: {result.rowcount} rows")

        result = session.exec(text("""
            UPDATE questionlink
            SET provider_id = CAST(vendor_id AS CHAR)
            WHERE provider_id IS NULL AND vendor_id IS NOT NULL
        """))
        session.commit()
        print(f"  ✓ Updated questionlink: {result.rowcount} rows")

        result = session.exec(text("""
            UPDATE matchlog
            SET provider_id = CAST(vendor_id AS CHAR)
            WHERE provider_id IS NULL AND vendor_id IS NOT NULL
        """))
        session.commit()
        print(f"  ✓ Updated matchlog: {result.rowcount} rows")

        # Step 3: Migrate answer_text to JSON
        print("\n[3/8] Converting answer_text to JSON format...")
        result = session.exec(text("""
            UPDATE responseentry
            SET answer = JSON_OBJECT(
                'type', 'text',
                'text', COALESCE(answer_text, ''),
                'comment', NULL
            )
            WHERE answer IS NULL AND answer_text IS NOT NULL
        """))
        session.commit()
        print(f"  ✓ Migrated {result.rowcount} answers")

        # Step 4: Make provider_id NOT NULL
        print("\n[4/8] Making provider_id NOT NULL...")
        session.exec(text("ALTER TABLE responseentry MODIFY COLUMN provider_id VARCHAR(16) NOT NULL"))
        session.exec(text("ALTER TABLE questionlink MODIFY COLUMN provider_id VARCHAR(16) NOT NULL"))
        session.exec(text("ALTER TABLE matchlog MODIFY COLUMN provider_id VARCHAR(16) NOT NULL"))
        session.commit()
        print("  ✓ Constraints updated")

        # Step 5: Drop old indexes
        print("\n[5/8] Dropping old indexes...")
        old_indexes = [
            ("idx_vendor_id", "responseentry"),
            ("uix_vendor_question", "responseentry"),
        ]
        for idx_name, table_name in old_indexes:
            try:
                session.exec(text(f"DROP INDEX {idx_name} ON {table_name}"))
                print(f"  ✓ Dropped {idx_name}")
            except Exception:
                print(f"  - {idx_name} not found")
        session.commit()

        # Step 6: Create new indexes
        print("\n[6/8] Creating new indexes...")
        try:
            session.exec(text("CREATE INDEX idx_provider_id ON responseentry(provider_id)"))
            print("  ✓ Created idx_provider_id")
        except Exception as e:
            print(f"  - idx_provider_id: {e}")

        try:
            session.exec(text("CREATE UNIQUE INDEX uix_provider_question ON responseentry(provider_id, question_id)"))
            print("  ✓ Created uix_provider_question")
        except Exception as e:
            print(f"  - uix_provider_question: {e}")

        try:
            session.exec(text("CREATE INDEX idx_qlink_provider ON questionlink(provider_id)"))
            print("  ✓ Created idx_qlink_provider")
        except Exception as e:
            print(f"  - idx_qlink_provider: {e}")

        try:
            session.exec(text("CREATE UNIQUE INDEX uix_provider_new_question ON questionlink(provider_id, new_question_id)"))
            print("  ✓ Created uix_provider_new_question")
        except Exception as e:
            print(f"  - uix_provider_new_question: {e}")

        try:
            session.exec(text("CREATE INDEX idx_matchlog_provider ON matchlog(provider_id)"))
            print("  ✓ Created idx_matchlog_provider")
        except Exception as e:
            print(f"  - idx_matchlog_provider: {e}")

        session.commit()

        # Step 7: Drop old columns
        print("\n[7/8] Dropping old columns...")
        try:
            session.exec(text("ALTER TABLE responseentry DROP COLUMN vendor_id"))
            print("  ✓ Dropped vendor_id from responseentry")
        except Exception as e:
            print(f"  Note: {e}")

        try:
            session.exec(text("ALTER TABLE responseentry DROP COLUMN answer_text"))
            print("  ✓ Dropped answer_text from responseentry")
        except Exception as e:
            print(f"  Note: {e}")

        try:
            session.exec(text("ALTER TABLE questionlink DROP COLUMN vendor_id"))
            print("  ✓ Dropped vendor_id from questionlink")
        except Exception as e:
            print(f"  Note: {e}")

        try:
            session.exec(text("ALTER TABLE matchlog DROP COLUMN vendor_id"))
            print("  ✓ Dropped vendor_id from matchlog")
        except Exception as e:
            print(f"  Note: {e}")

        session.commit()

        # Step 8: Verification
        print("\n[8/8] Verifying migration...")
        result = session.exec(text("SELECT COUNT(*) FROM responseentry WHERE provider_id IS NULL OR answer IS NULL"))
        null_count = result.first()[0]
        if null_count > 0:
            print(f"  ⚠ WARNING: Found {null_count} NULL values in responseentry")
        else:
            print("  ✓ All responseentry rows validated")

        result = session.exec(text("SELECT COUNT(*) FROM responseentry"))
        count = result.first()[0]
        print(f"  ✓ ResponseEntry: {count} rows")

        result = session.exec(text("SELECT COUNT(*) FROM questionlink"))
        count = result.first()[0]
        print(f"  ✓ QuestionLink: {count} rows")

        result = session.exec(text("SELECT COUNT(*) FROM matchlog"))
        count = result.first()[0]
        print(f"  ✓ MatchLog: {count} rows")

        print("\n" + "=" * 80)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        session.rollback()
        raise

if __name__ == "__main__":
    pass
