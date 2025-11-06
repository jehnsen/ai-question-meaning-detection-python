"""
Reset Database Tool - Effortless-Respond API

This script provides two options for database management:

1. Reset Database (Option 1):
   - Drops ALL tables (responseentry, questionlink, analyticsevent, usagemetrics)
   - Recreates all tables with correct schema
   - Use when: Changing embedding model/dimensions, schema changes, or starting fresh

2. Clear Data Only (Option 2):
   - Deletes all data but keeps table structure
   - Safer option that preserves schema
   - Use when: Testing with fresh data without schema changes

Usage:
    python reset_database.py 1    # Reset database (auto-confirm)
    python reset_database.py 2    # Clear data only (auto-confirm)
    python reset_database.py      # Interactive mode

IMPORTANT: Always backup your data before running this script!
"""

from sqlalchemy import create_engine, text
from sqlmodel import SQLModel
import os
from dotenv import load_dotenv
import sys

# Load environment variables (override system env vars)
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

# Detect database type
is_mysql = DATABASE_URL and "mysql" in DATABASE_URL.lower()

def reset_database(auto_confirm=False):
    """Drop all tables and recreate them."""
    print("=" * 60)
    print("DATABASE RESET TOOL")
    print("=" * 60)
    print("\nWARNING: This will delete ALL data!")
    print("  - All responses")
    print("  - All question links")
    print("  - All embeddings")
    print("  - All analytics events")
    print("  - All usage metrics")

    if not auto_confirm:
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    print("\nConnecting to database...")
    engine = create_engine(DATABASE_URL)

    # Import models to register them
    from main import ResponseEntry, QuestionLink

    # Try to import analytics models if they exist
    try:
        from main import AnalyticsEvent, UsageMetrics
        has_analytics = True
    except ImportError:
        has_analytics = False

    print("Dropping all tables...")
    SQLModel.metadata.drop_all(engine)

    print("Creating fresh tables...")
    # MySQL doesn't need pgvector extension
    SQLModel.metadata.create_all(engine)

    print("\n" + "=" * 60)
    print("SUCCESS: Database reset complete!")
    print("=" * 60)
    print("\nTables created:")
    print("  [OK] responseentry (canonical questions & answers)")
    print("  [OK] questionlink (saved question links)")
    if has_analytics:
        print("  [OK] analyticsevent (analytics tracking)")
        print("  [OK] usagemetrics (daily aggregations)")
    print("\nNext steps:")
    print("  1. Start the API: python main.py")
    print("  2. Add new responses via /create-response")
    print("  3. Test with /batch-process-questionnaire")


def just_clear_data(auto_confirm=False):
    """Clear data without dropping tables (safer)."""
    print("=" * 60)
    print("CLEAR DATA TOOL")
    print("=" * 60)
    print("\nThis will delete all data but keep table structure.")
    print("  - Question links")
    print("  - Responses")
    print("  - Analytics events")
    print("  - Usage metrics")

    if not auto_confirm:
        response = input("\nContinue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    print("\nConnecting to database...")
    engine = create_engine(DATABASE_URL)

    # Try to import analytics models to check if they exist
    try:
        from main import AnalyticsEvent, UsageMetrics
        has_analytics = True
    except ImportError:
        has_analytics = False

    with engine.connect() as conn:
        print("Deleting all question links...")
        conn.execute(text("DELETE FROM questionlink"))

        print("Deleting all responses...")
        conn.execute(text("DELETE FROM responseentry"))

        if has_analytics:
            print("Deleting all analytics events...")
            conn.execute(text("DELETE FROM analyticsevent"))

            print("Deleting all usage metrics...")
            conn.execute(text("DELETE FROM usagemetrics"))

        conn.commit()

    print("\n" + "=" * 60)
    print("SUCCESS: Data cleared!")
    print("=" * 60)
    print("\nAll data has been deleted. Tables remain intact.")


if __name__ == "__main__":
    import sys

    # Check for command-line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("\nChoose an option:")
        print("  1. Reset database (drop and recreate tables)")
        print("  2. Clear data only (keep table structure)")
        print("  3. Cancel")
        choice = input("\nYour choice (1/2/3): ")

    if choice == "1":
        reset_database(auto_confirm=(len(sys.argv) > 1))
    elif choice == "2":
        just_clear_data(auto_confirm=(len(sys.argv) > 1))
    else:
        print("Cancelled.")
