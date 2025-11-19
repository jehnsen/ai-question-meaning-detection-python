"""
Reset and initialize database with correct schema.

This script will:
1. Drop all existing tables
2. Recreate them with the correct types (LONGBLOB for embeddings)
"""
from app.services.database import engine
from sqlalchemy import text
from app.services import init_db


def reset_database():
    """
    Drop all tables and recreate with correct schema.

    WARNING: This will delete all data!
    """
    print("⚠️  WARNING: This will delete all existing data!")
    print("Tables to be dropped: responseentry, questionlink, matchlog")

    confirm = input("Type 'YES' to continue: ")

    if confirm != "YES":
        print("Aborted.")
        return

    print("\nStarting database reset...")

    with engine.connect() as connection:
        trans = connection.begin()

        try:
            # Drop tables in correct order (respecting foreign keys)
            print("Dropping tables...")

            # Drop questionlink first (has foreign key to responseentry)
            connection.execute(text("DROP TABLE IF EXISTS questionlink"))
            print("✓ Dropped questionlink")

            # Drop matchlog (no foreign keys)
            connection.execute(text("DROP TABLE IF EXISTS matchlog"))
            print("✓ Dropped matchlog")

            # Drop responseentry last
            connection.execute(text("DROP TABLE IF EXISTS responseentry"))
            print("✓ Dropped responseentry")

            trans.commit()
            print("\n✓ All tables dropped successfully")

        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error dropping tables: {e}")
            raise

    # Recreate tables with correct schema
    print("\nRecreating tables with correct schema...")
    init_db()
    print("\n✓ Database initialized successfully!")
    print("\nTables created:")
    print("  - responseentry (with LONGBLOB for embeddings)")
    print("  - questionlink (with foreign key to responseentry)")
    print("  - matchlog (for analytics)")


if __name__ == "__main__":
    reset_database()
