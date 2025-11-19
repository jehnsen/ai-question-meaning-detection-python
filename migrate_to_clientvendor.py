"""
Database Migration Script: Vendor ID to Client-Vendor Relationship

This script migrates the database from using a simple vendor_id string
to using client-vendor relationships with a foreign key to the clientvendor table.

Changes:
1. ResponseEntry: vendor_id (str) -> client_vendor_id (int, FK)
2. ResponseEntry: answer_text (text) -> answer (JSON with type, text, comment)
3. QuestionLink: vendor_id (str) -> client_vendor_id (int, FK)
4. MatchLog: vendor_id (str) -> client_vendor_id (int, FK)

Prerequisites:
- Backup your database before running this script
- Ensure the clientvendor table exists with columns: id, clientid, providerid
- Update DATABASE_URL in .env file

Usage:
    python migrate_to_clientvendor.py
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
    print("DATABASE MIGRATION: Vendor ID -> Client-Vendor Relationship")
    print("=" * 80 + "\n")

    with Session(engine) as session:
        try:
            # Step 1: Add new columns to existing tables
            print("\n[Step 1/8] Adding new columns to tables...")
            add_new_columns(session)

            # Step 2: Migrate data from vendor_id to client_vendor_id
            print("\n[Step 2/8] Migrating vendor_id data to client_vendor_id...")
            migrate_vendor_ids(session)

            # Step 3: Migrate answer_text to answer JSON format
            print("\n[Step 3/8] Migrating answer_text to answer JSON format...")
            migrate_answer_format(session)

            # Step 4: Drop old vendor_id columns
            print("\n[Step 4/8] Dropping old vendor_id columns...")
            drop_old_columns(session)

            # Step 5: Drop old answer_text column
            print("\n[Step 5/8] Dropping old answer_text column...")
            drop_answer_text_column(session)

            # Step 6: Add foreign key constraints
            print("\n[Step 6/8] Adding foreign key constraints...")
            add_foreign_keys(session)

            # Step 7: Update indexes
            print("\n[Step 7/8] Updating indexes...")
            update_indexes(session)

            # Step 8: Verify migration
            print("\n[Step 8/8] Verifying migration...")
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
    # Add client_vendor_id to responseentry
    session.exec(text("""
        ALTER TABLE responseentry
        ADD COLUMN client_vendor_id INT NULL
    """))

    # Add answer column to responseentry (JSON format)
    session.exec(text("""
        ALTER TABLE responseentry
        ADD COLUMN answer LONGTEXT NULL
    """))

    # Add client_vendor_id to questionlink
    session.exec(text("""
        ALTER TABLE questionlink
        ADD COLUMN client_vendor_id INT NULL
    """))

    # Add client_vendor_id to matchlog
    session.exec(text("""
        ALTER TABLE matchlog
        ADD COLUMN client_vendor_id INT NULL
    """))

    session.commit()
    print("✓ New columns added successfully")


def migrate_vendor_ids(session: Session):
    """Migrate vendor_id string values to client_vendor_id foreign keys."""

    # Get all unique vendor_ids from responseentry
    vendor_ids_result = session.exec(text("""
        SELECT DISTINCT vendor_id FROM responseentry
    """))
    vendor_ids = [row[0] for row in vendor_ids_result]

    print(f"  Found {len(vendor_ids)} unique vendor IDs to migrate")

    # For each vendor_id, create or find a clientvendor entry
    # Assuming vendor_id maps to both clientid and providerid for this migration
    # You may need to adjust this logic based on your data structure
    for vendor_id in vendor_ids:
        # Check if clientvendor entry exists
        check_query = text("""
            SELECT id FROM clientvendor
            WHERE clientid = :vendor_id AND providerid = :vendor_id
        """)
        result = session.exec(check_query, {"vendor_id": vendor_id}).first()

        if result:
            client_vendor_id = result[0]
        else:
            # Create new clientvendor entry
            insert_query = text("""
                INSERT INTO clientvendor (clientid, providerid)
                VALUES (:vendor_id, :vendor_id)
            """)
            session.exec(insert_query, {"vendor_id": vendor_id})
            session.commit()

            # Get the inserted ID
            client_vendor_id = session.exec(text("SELECT LAST_INSERT_ID()")).first()[0]

        # Update responseentry
        session.exec(text("""
            UPDATE responseentry
            SET client_vendor_id = :client_vendor_id
            WHERE vendor_id = :vendor_id
        """), {"client_vendor_id": client_vendor_id, "vendor_id": vendor_id})

        # Update questionlink
        session.exec(text("""
            UPDATE questionlink
            SET client_vendor_id = :client_vendor_id
            WHERE vendor_id = :vendor_id
        """), {"client_vendor_id": client_vendor_id, "vendor_id": vendor_id})

        # Update matchlog
        session.exec(text("""
            UPDATE matchlog
            SET client_vendor_id = :client_vendor_id
            WHERE vendor_id = :vendor_id
        """), {"client_vendor_id": client_vendor_id, "vendor_id": vendor_id})

    session.commit()
    print("✓ Vendor IDs migrated successfully")


def migrate_answer_format(session: Session):
    """Migrate answer_text to answer JSON format."""

    # Get all responses with answer_text
    result = session.exec(text("""
        SELECT id, answer_text FROM responseentry
    """))

    count = 0
    for row in result:
        response_id = row[0]
        answer_text = row[1]

        # Convert to new JSON format
        answer_json = json.dumps({
            "type": "text",
            "text": answer_text if answer_text else "",
            "comment": None
        })

        # Update the answer column
        session.exec(text("""
            UPDATE responseentry
            SET answer = :answer_json
            WHERE id = :response_id
        """), {"answer_json": answer_json, "response_id": response_id})

        count += 1

    session.commit()
    print(f"✓ Migrated {count} answers to new JSON format")


def drop_old_columns(session: Session):
    """Drop old vendor_id columns."""

    # Drop vendor_id from responseentry
    session.exec(text("""
        ALTER TABLE responseentry
        DROP COLUMN vendor_id
    """))

    # Drop vendor_id from questionlink
    session.exec(text("""
        ALTER TABLE questionlink
        DROP COLUMN vendor_id
    """))

    # Drop vendor_id from matchlog
    session.exec(text("""
        ALTER TABLE matchlog
        DROP COLUMN vendor_id
    """))

    session.commit()
    print("✓ Old vendor_id columns dropped successfully")


def drop_answer_text_column(session: Session):
    """Drop old answer_text column."""

    session.exec(text("""
        ALTER TABLE responseentry
        DROP COLUMN answer_text
    """))

    session.commit()
    print("✓ Old answer_text column dropped successfully")


def add_foreign_keys(session: Session):
    """Add foreign key constraints."""

    # Make client_vendor_id NOT NULL first
    session.exec(text("""
        ALTER TABLE responseentry
        MODIFY COLUMN client_vendor_id INT NOT NULL
    """))

    session.exec(text("""
        ALTER TABLE questionlink
        MODIFY COLUMN client_vendor_id INT NOT NULL
    """))

    session.exec(text("""
        ALTER TABLE matchlog
        MODIFY COLUMN client_vendor_id INT NOT NULL
    """))

    # Add foreign key constraints
    try:
        session.exec(text("""
            ALTER TABLE responseentry
            ADD CONSTRAINT fk_responseentry_clientvendor
            FOREIGN KEY (client_vendor_id) REFERENCES clientvendor(id)
        """))
    except Exception as e:
        print(f"  Warning: Could not add FK for responseentry: {e}")

    try:
        session.exec(text("""
            ALTER TABLE questionlink
            ADD CONSTRAINT fk_questionlink_clientvendor
            FOREIGN KEY (client_vendor_id) REFERENCES clientvendor(id)
        """))
    except Exception as e:
        print(f"  Warning: Could not add FK for questionlink: {e}")

    try:
        session.exec(text("""
            ALTER TABLE matchlog
            ADD CONSTRAINT fk_matchlog_clientvendor
            FOREIGN KEY (client_vendor_id) REFERENCES clientvendor(id)
        """))
    except Exception as e:
        print(f"  Warning: Could not add FK for matchlog: {e}")

    session.commit()
    print("✓ Foreign key constraints added")


def update_indexes(session: Session):
    """Update indexes to use client_vendor_id instead of vendor_id."""

    # Drop old indexes
    try:
        session.exec(text("DROP INDEX idx_vendor_id ON responseentry"))
    except Exception:
        pass

    try:
        session.exec(text("DROP INDEX idx_qlink_vendor ON questionlink"))
    except Exception:
        pass

    try:
        session.exec(text("DROP INDEX idx_matchlog_vendor ON matchlog"))
    except Exception:
        pass

    # Create new indexes
    session.exec(text("""
        CREATE INDEX idx_client_vendor_id ON responseentry(client_vendor_id)
    """))

    session.exec(text("""
        CREATE INDEX idx_qlink_client_vendor ON questionlink(client_vendor_id)
    """))

    session.exec(text("""
        CREATE INDEX idx_matchlog_client_vendor ON matchlog(client_vendor_id)
    """))

    # Update unique constraints
    try:
        session.exec(text("DROP INDEX uix_vendor_question ON responseentry"))
    except Exception:
        pass

    session.exec(text("""
        CREATE UNIQUE INDEX uix_clientvendor_question
        ON responseentry(client_vendor_id, question_id)
    """))

    try:
        session.exec(text("DROP INDEX uix_vendor_new_question ON questionlink"))
    except Exception:
        pass

    session.exec(text("""
        CREATE UNIQUE INDEX uix_clientvendor_new_question
        ON questionlink(client_vendor_id, new_question_id)
    """))

    session.commit()
    print("✓ Indexes updated successfully")


def verify_migration(session: Session):
    """Verify that the migration was successful."""

    # Check responseentry table
    result = session.exec(text("""
        SELECT COUNT(*) as count FROM responseentry
        WHERE client_vendor_id IS NULL OR answer IS NULL
    """))
    null_count = result.first()[0]

    if null_count > 0:
        raise Exception(f"Found {null_count} rows with NULL client_vendor_id or answer in responseentry")

    # Check questionlink table
    result = session.exec(text("""
        SELECT COUNT(*) as count FROM questionlink
        WHERE client_vendor_id IS NULL
    """))
    null_count = result.first()[0]

    if null_count > 0:
        raise Exception(f"Found {null_count} rows with NULL client_vendor_id in questionlink")

    # Check matchlog table
    result = session.exec(text("""
        SELECT COUNT(*) as count FROM matchlog
        WHERE client_vendor_id IS NULL
    """))
    null_count = result.first()[0]

    if null_count > 0:
        raise Exception(f"Found {null_count} rows with NULL client_vendor_id in matchlog")

    # Print summary
    response_count = session.exec(text("SELECT COUNT(*) FROM responseentry")).first()[0]
    link_count = session.exec(text("SELECT COUNT(*) FROM questionlink")).first()[0]
    log_count = session.exec(text("SELECT COUNT(*) FROM matchlog")).first()[0]

    print(f"\n  ✓ ResponseEntry: {response_count} rows migrated")
    print(f"  ✓ QuestionLink: {link_count} rows migrated")
    print(f"  ✓ MatchLog: {log_count} rows migrated")
    print("  ✓ All data integrity checks passed")


if __name__ == "__main__":
    import sys

    print("\n⚠️  WARNING: This script will modify your database schema.")
    print("   Make sure you have backed up your database before proceeding.")
    response = input("\nDo you want to continue? (yes/no): ")

    if response.lower() != "yes":
        print("Migration cancelled.")
        sys.exit(0)

    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
