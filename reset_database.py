"""
Reset database - Clear all data and recreate tables
Use this when you change the embedding model or dimension
"""

from sqlalchemy import create_engine, text
from sqlmodel import SQLModel
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def reset_database(auto_confirm=False):
    """Drop all tables and recreate them."""
    print("=" * 60)
    print("DATABASE RESET TOOL")
    print("=" * 60)
    print("\nWARNING: This will delete ALL data!")
    print("  - All responses")
    print("  - All question links")
    print("  - All embeddings")

    if not auto_confirm:
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    print("\nConnecting to database...")
    engine = create_engine(DATABASE_URL)

    # Import models to register them
    from main import ResponseEntry, QuestionLink

    print("Dropping all tables...")
    SQLModel.metadata.drop_all(engine)

    print("Creating fresh tables...")
    SQLModel.metadata.create_all(engine)

    print("\n" + "=" * 60)
    print("SUCCESS: Database reset complete!")
    print("=" * 60)
    print("\nAll tables have been recreated with the correct schema.")
    print("You can now start fresh with your data.")
    print("\nNext steps:")
    print("  1. Start the API: python main.py")
    print("  2. Add new responses via /create-new-response")
    print("  3. Test with /process-question")


def just_clear_data(auto_confirm=False):
    """Clear data without dropping tables (safer)."""
    print("=" * 60)
    print("CLEAR DATA TOOL")
    print("=" * 60)
    print("\nThis will delete all data but keep table structure.")

    if not auto_confirm:
        response = input("\nContinue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

    print("\nConnecting to database...")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Deleting all question links...")
        conn.execute(text("DELETE FROM questionlink"))

        print("Deleting all responses...")
        conn.execute(text("DELETE FROM responseentry"))

        conn.commit()

    print("\n" + "=" * 60)
    print("SUCCESS: Data cleared!")
    print("=" * 60)


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
