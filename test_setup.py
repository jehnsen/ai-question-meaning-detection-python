"""
Test script to verify the database connection and setup.
Run this before starting the main application.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_database_connection():
    """Test if we can connect to PostgreSQL."""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not found in .env file")
        return False

    print(f"Database URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"[OK] Connected to PostgreSQL successfully!")
            print(f"  Version: {version}")
            return True
    except Exception as e:
        print(f"[FAILED] Failed to connect to database:")
        print(f"  Error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check your credentials in .env file")
        print("  3. Verify the database 'effortless_respond' exists")
        return False


def test_pgvector_extension():
    """Test if pgvector extension is available."""
    print("\n" + "=" * 60)
    print("Testing pgvector Extension")
    print("=" * 60)

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Try to create the extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

            # Check if it's installed
            result = conn.execute(
                text("SELECT * FROM pg_extension WHERE extname = 'vector';")
            )

            if result.first():
                print("[OK] pgvector extension is installed and ready!")
                return True
            else:
                print("[FAILED] pgvector extension not found")
                return False

    except Exception as e:
        print(f"[FAILED] Failed to setup pgvector extension:")
        print(f"  Error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Install pgvector: https://github.com/pgvector/pgvector")
        print("  2. Or use Docker: docker-compose up -d")
        return False


def test_ai_model():
    """Test if we can load the AI model."""
    print("\n" + "=" * 60)
    print("Testing AI Model")
    print("=" * 60)

    try:
        from sentence_transformers import SentenceTransformer

        print("Loading model 'all-MiniLM-L6-v2'...")
        print("(First run will download ~80MB)")

        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Test embedding
        test_text = "This is a test sentence"
        embedding = model.encode(test_text)

        print(f"[OK] AI model loaded successfully!")
        print(f"  Embedding dimension: {len(embedding)}")

        return True

    except Exception as e:
        print(f"[FAILED] Failed to load AI model:")
        print(f"  Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\nRunning Setup Tests...\n")

    tests_passed = 0
    total_tests = 3

    if test_database_connection():
        tests_passed += 1

    if test_pgvector_extension():
        tests_passed += 1

    if test_ai_model():
        tests_passed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} passed")
    print("=" * 60)

    if tests_passed == total_tests:
        print("\nAll tests passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Run: python main.py")
        print("  2. Open: http://localhost:8000/docs")
        return 0
    else:
        print("\nSome tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
