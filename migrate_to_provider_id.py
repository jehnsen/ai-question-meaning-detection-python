"""
Database Migration Script: Vendor ID to Provider ID with Answer Format

This script migrates the database from using vendor_id to provider_id
and converts answer_text to structured JSON answer format.

Changes:
1. ResponseEntry: vendor_id (str/binary) -> provider_id (VARCHAR(16))
2. ResponseEntry: answer_text (text) -> answer (JSON with type, text, comment)
3. QuestionLink: vendor_id (str/binary) -> provider_id (VARCHAR(16))
4. MatchLog: vendor_id (str/binary) -> provider_id (VARCHAR(16))

Prerequisites:
- Backup your database before running this script
- Update DATABASE_URL in .env file

Usage:
    python migrate_to_provider_id.py
"""

import os
import json
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, text

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def run_migration():
    """Run the complete migration process."""
    print("\n" + "=" * 80)
    print("DATABASE MIGRATION: Vendor ID -> Provider ID + Answer Format")
    print("=" * 80 + "\n")

    with Session(engine) as session:
        try:
            # Step 1: Add new columns to existing tables
            print("\n[Step 1/6] Adding new columns to tables...")
            add_new_columns(session)

            # Step 2: Migrate data from vendor_id to provider_id
            print("\n[Step 2/6] Migrating vendor_id data to provider_id...")
            migrate_vendor_to_provider(session)

            # Step 3: Migrate answer_text to answer JSON format
            print("\n[Step 3/6] Migrating answer_text to answer JSON format...")
            migrate_answer_format(session)

            # Step 4: Drop old columns and make provider_id NOT NULL
            print("\n[Step 4/6] Dropping old columns and updating constraints...")
            finalize_schema(session)

            # Step 5: Update indexes
            print("\n[Step 5/6] Updating indexes...")
            update_indexes(session)

            # Step 6: Verify migration
            print("\n[Step 6/6] Verifying migration...")
            verify_migration(session)

            print("\n" + "=" * 80)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 80 + "\n")

        except Exception as e:
            print(f"\n❌ ERROR: Migration failed: {e}")
            print("Rolling back changes...")
            session.rollback()
            raise


def add_new_columns(session: Session):
    """Add new columns to tables."""
    print("  Adding provider_id to responseentry...")
    try:
        session.exec(text("""
            ALTER TABLE responseentry
            ADD COLUMN provider_id VARCHAR(16) NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not add provider_id to responseentry: {e}")

    print("  Adding answer to responseentry...")
    try:
        session.exec(text("""
            ALTER TABLE responseentry
            ADD COLUMN answer LONGTEXT NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not add answer to responseentry: {e}")

    print("  Adding provider_id to questionlink...")
    try:
        session.exec(text("""
            ALTER TABLE questionlink
            ADD COLUMN provider_id VARCHAR(16) NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not add provider_id to questionlink: {e}")

    print("  Adding provider_id to matchlog...")
    try:
        session.exec(text("""
            ALTER TABLE matchlog
            ADD COLUMN provider_id VARCHAR(16) NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not add provider_id to matchlog: {e}")

    session.commit()
    print("✓ New columns added successfully")


def migrate_vendor_to_provider(session: Session):
    """Migrate vendor_id to provider_id."""

    print("  Migrating responseentry vendor_id to provider_id...")
    # Handle binary vendor_id
    result = session.exec(text("""
        UPDATE responseentry
        SET provider_id = CAST(vendor_id AS CHAR)
        WHERE provider_id IS NULL AND vendor_id IS NOT NULL
    """))
    session.commit()
    print(f"  ✓ Updated {result.rowcount} rows in responseentry")

    print("  Migrating questionlink vendor_id to provider_id...")
    result = session.exec(text("""
        UPDATE questionlink
        SET provider_id = CAST(vendor_id AS CHAR)
        WHERE provider_id IS NULL AND vendor_id IS NOT NULL
    """))
    session.commit()
    print(f"  ✓ Updated {result.rowcount} rows in questionlink")

    print("  Migrating matchlog vendor_id to provider_id...")
    result = session.exec(text("""
        UPDATE matchlog
        SET provider_id = CAST(vendor_id AS CHAR)
        WHERE provider_id IS NULL AND vendor_id IS NOT NULL
    """))
    session.commit()
    print(f"  ✓ Updated {result.rowcount} rows in matchlog")

    print("✓ Vendor ID migration completed")


def migrate_answer_format(session: Session):
    """Migrate answer_text to answer JSON format."""

    print("  Converting answer_text to JSON format...")

    # Get count of rows to migrate
    count_result = session.exec(text("""
        SELECT COUNT(*) as count FROM responseentry
        WHERE answer IS NULL AND answer_text IS NOT NULL
    """))
    count = count_result.first()[0]

    if count == 0:
        print("  ℹ No rows to migrate (answer_text already migrated or empty)")
        return

    print(f"  Migrating {count} answers...")

    # Update with JSON format
    session.exec(text("""
        UPDATE responseentry
        SET answer = JSON_OBJECT(
            'type', 'text',
            'text', COALESCE(answer_text, ''),
            'comment', NULL
        )
        WHERE answer IS NULL AND answer_text IS NOT NULL
    """))

    session.commit()
    print(f"✓ Migrated {count} answers to new JSON format")


def finalize_schema(session: Session):
    """Drop old columns and finalize schema."""

    # Make provider_id NOT NULL
    print("  Making provider_id NOT NULL in responseentry...")
    try:
        session.exec(text("""
            ALTER TABLE responseentry
            MODIFY COLUMN provider_id VARCHAR(16) NOT NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not modify provider_id in responseentry: {e}")

    print("  Making provider_id NOT NULL in questionlink...")
    try:
        session.exec(text("""
            ALTER TABLE questionlink
            MODIFY COLUMN provider_id VARCHAR(16) NOT NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not modify provider_id in questionlink: {e}")

    print("  Making provider_id NOT NULL in matchlog...")
    try:
        session.exec(text("""
            ALTER TABLE matchlog
            MODIFY COLUMN provider_id VARCHAR(16) NOT NULL
        """))
    except Exception as e:
        print(f"  Warning: Could not modify provider_id in matchlog: {e}")

    # Drop old vendor_id columns
    print("  Dropping old vendor_id columns...")
    try:
        session.exec(text("ALTER TABLE responseentry DROP COLUMN vendor_id"))
        print("  ✓ Dropped vendor_id from responseentry")
    except Exception as e:
        print(f"  Warning: Could not drop vendor_id from responseentry: {e}")

    try:
        session.exec(text("ALTER TABLE questionlink DROP COLUMN vendor_id"))
        print("  ✓ Dropped vendor_id from questionlink")
    except Exception as e:
        print(f"  Warning: Could not drop vendor_id from questionlink: {e}")

    try:
        session.exec(text("ALTER TABLE matchlog DROP COLUMN vendor_id"))
        print("  ✓ Dropped vendor_id from matchlog")
    except Exception as e:
        print(f"  Warning: Could not drop vendor_id from matchlog: {e}")

    # Drop old answer_text column
    print("  Dropping old answer_text column...")
    try:
        session.exec(text("ALTER TABLE responseentry DROP COLUMN answer_text"))
        print("  ✓ Dropped answer_text from responseentry")
    except Exception as e:
        print(f"  Warning: Could not drop answer_text: {e}")

    session.commit()
    print("✓ Schema finalization completed")


def update_indexes(session: Session):
    """Update indexes to use provider_id."""

    # Drop old indexes if they exist
    print("  Dropping old indexes...")
    old_indexes = [
        ("idx_vendor_id", "responseentry"),
        ("idx_qlink_vendor", "questionlink"),
        ("idx_qlink_client_vendor", "questionlink"),
        ("idx_matchlog_vendor", "matchlog"),
        ("idx_matchlog_client_vendor", "matchlog"),
        ("uix_vendor_question", "responseentry"),
        ("uix_vendor_new_question", "questionlink"),
        ("uix_clientvendor_question", "responseentry"),
        ("uix_clientvendor_new_question", "questionlink"),
    ]

    for index_name, table_name in old_indexes:
        try:
            session.exec(text(f"DROP INDEX {index_name} ON {table_name}"))
            print(f"  ✓ Dropped index {index_name}")
        except Exception as e:
            print(f"  ℹ Index {index_name} not found (already dropped or doesn't exist)")

    # Create new indexes
    print("  Creating new indexes...")

    try:
        session.exec(text("""
            CREATE INDEX idx_provider_id ON responseentry(provider_id)
        """))
        print("  ✓ Created idx_provider_id on responseentry")
    except Exception as e:
        print(f"  Warning: Could not create idx_provider_id on responseentry: {e}")

    try:
        session.exec(text("""
            CREATE INDEX idx_qlink_provider ON questionlink(provider_id)
        """))
        print("  ✓ Created idx_qlink_provider on questionlink")
    except Exception as e:
        print(f"  Warning: Could not create idx_qlink_provider on questionlink: {e}")

    try:
        session.exec(text("""
            CREATE INDEX idx_matchlog_provider ON matchlog(provider_id)
        """))
        print("  ✓ Created idx_matchlog_provider on matchlog")
    except Exception as e:
        print(f"  Warning: Could not create idx_matchlog_provider on matchlog: {e}")

    # Create unique constraints
    print("  Creating unique constraints...")

    try:
        session.exec(text("""
            CREATE UNIQUE INDEX uix_provider_question
            ON responseentry(provider_id, question_id)
        """))
        print("  ✓ Created uix_provider_question on responseentry")
    except Exception as e:
        print(f"  Warning: Could not create uix_provider_question: {e}")

    try:
        session.exec(text("""
            CREATE UNIQUE INDEX uix_provider_new_question
            ON questionlink(provider_id, new_question_id)
        """))
        print("  ✓ Created uix_provider_new_question on questionlink")
    except Exception as e:
        print(f"  Warning: Could not create uix_provider_new_question: {e}")

    session.commit()
    print("✓ Indexes updated successfully")


def verify_migration(session: Session):
    """Verify that the migration was successful."""

    print("  Checking responseentry table...")
    result = session.exec(text("""
        SELECT COUNT(*) as count FROM responseentry
        WHERE provider_id IS NULL OR answer IS NULL
    """))
    null_count = result.first()[0]

    if null_count > 0:
        raise Exception(f"Found {null_count} rows with NULL provider_id or answer in responseentry")

    response_count = session.exec(text("SELECT COUNT(*) FROM responseentry")).first()[0]
    print(f"  ✓ ResponseEntry: {response_count} rows migrated")

    print("  Checking questionlink table...")
    result = session.exec(text("""
        SELECT COUNT(*) as count FROM questionlink
        WHERE provider_id IS NULL
    """))
    null_count = result.first()[0]

    if null_count > 0:
        raise Exception(f"Found {null_count} rows with NULL provider_id in questionlink")

    link_count = session.exec(text("SELECT COUNT(*) FROM questionlink")).first()[0]
    print(f"  ✓ QuestionLink: {link_count} rows migrated")

    print("  Checking matchlog table...")
    result = session.exec(text("""
        SELECT COUNT(*) as count FROM matchlog
        WHERE provider_id IS NULL
    """))
    null_count = result.first()[0]

    if null_count > 0:
        raise Exception(f"Found {null_count} rows with NULL provider_id in matchlog")

    log_count = session.exec(text("SELECT COUNT(*) FROM matchlog")).first()[0]
    print(f"  ✓ MatchLog: {log_count} rows migrated")

    print("  ✓ All data integrity checks passed")


if __name__ == "__main__":
    import sys

    print("\n⚠️  WARNING: This script will modify your database schema.")
    print("   Make sure you have backed up your database before proceeding.")
    print("\nChanges that will be made:")
    print("   1. Add provider_id column to responseentry, questionlink, matchlog")
    print("   2. Convert answer_text to JSON answer format")
    print("   3. Drop old vendor_id columns")
    print("   4. Update indexes and constraints")

    response = input("\nDo you want to continue? (yes/no): ")

    if response.lower() != "yes":
        print("Migration cancelled.")
        sys.exit(0)

    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
