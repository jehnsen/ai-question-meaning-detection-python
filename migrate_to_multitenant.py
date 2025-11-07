"""
Migration script to add multi-tenant support (vendor_id) to existing database.

This script:
1. Adds vendor_id column to responseentry table
2. Adds vendor_id column to questionlink table
3. Sets default vendor_id for existing data
4. Removes old unique constraint on question_id
5. Adds composite unique constraint on (vendor_id, question_id)

Usage:
    python migrate_to_multitenant.py
"""

import pymysql
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not found in environment")
    exit(1)

# Parse MySQL connection string
# Format: mysql+pymysql://user:password@host:port/database
db_url = DATABASE_URL.replace("mysql+pymysql://", "")
parts = db_url.split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")
host_port = host_db[0].split(":")

username = user_pass[0]
password = user_pass[1] if len(user_pass) > 1 else ""
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 3306
database = host_db[1]

print("=" * 60)
print("MULTI-TENANT MIGRATION SCRIPT")
print("=" * 60)
print(f"\nDatabase: {database}")
print(f"Host: {host}:{port}")
print("\nThis will:")
print("  1. Add vendor_id column to responseentry table")
print("  2. Add vendor_id column to questionlink table")
print("  3. Set default vendor_id='DEFAULT' for existing records")
print("  4. Update unique constraints for multi-tenancy")
print("\n" + "=" * 60)

# Auto-proceed for automated execution
# Uncomment the lines below to enable interactive confirmation
# response = input("\nProceed with migration? (yes/no): ")
# if response.lower() != "yes":
#     print("Migration cancelled.")
#     exit(0)

print("\nProceeding with migration...")

try:
    # Connect to database
    print("\nConnecting to database...")
    connection = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        charset='utf8mb4'
    )

    cursor = connection.cursor()

    # Step 1: Add vendor_id to responseentry
    print("\n[1/5] Adding vendor_id column to responseentry...")
    try:
        cursor.execute("""
            ALTER TABLE responseentry
            ADD COLUMN vendor_id VARCHAR(255) NOT NULL DEFAULT 'DEFAULT' AFTER id
        """)
        cursor.execute("ALTER TABLE responseentry ADD INDEX idx_vendor_id (vendor_id)")
        connection.commit()
        print("  [OK] vendor_id added to responseentry")
    except pymysql.err.OperationalError as e:
        if "Duplicate column name" in str(e):
            print("  [SKIP] vendor_id column already exists")
        else:
            raise

    # Step 2: Remove old unique constraint on question_id
    print("\n[2/5] Removing old unique constraint on question_id...")
    try:
        cursor.execute("ALTER TABLE responseentry DROP INDEX ix_responseentry_question_id")
        connection.commit()
        print("  [OK] Old unique constraint removed")
    except pymysql.err.OperationalError as e:
        if "check that column/key exists" in str(e).lower():
            print("  [SKIP] Constraint already removed")
        else:
            raise

    # Step 3: Add composite unique constraint
    print("\n[3/5] Adding composite unique constraint (vendor_id, question_id)...")
    try:
        cursor.execute("""
            ALTER TABLE responseentry
            ADD UNIQUE INDEX uix_vendor_question (vendor_id, question_id)
        """)
        connection.commit()
        print("  [OK] Composite unique constraint added")
    except pymysql.err.OperationalError as e:
        if "Duplicate key name" in str(e):
            print("  [SKIP] Composite constraint already exists")
        else:
            raise

    # Step 4: Add vendor_id to questionlink
    print("\n[4/5] Adding vendor_id column to questionlink...")
    try:
        cursor.execute("""
            ALTER TABLE questionlink
            ADD COLUMN vendor_id VARCHAR(255) NOT NULL DEFAULT 'DEFAULT' AFTER id
        """)
        cursor.execute("ALTER TABLE questionlink ADD INDEX idx_qlink_vendor (vendor_id)")
        connection.commit()
        print("  [OK] vendor_id added to questionlink")
    except pymysql.err.OperationalError as e:
        if "Duplicate column name" in str(e):
            print("  [SKIP] vendor_id column already exists")
        else:
            raise

    # Step 5: Remove old unique constraint on new_question_id
    print("\n[5/5] Updating questionlink constraints...")
    try:
        cursor.execute("ALTER TABLE questionlink DROP INDEX ix_questionlink_new_question_id")
        connection.commit()
        print("  [OK] Old questionlink constraint removed")
    except pymysql.err.OperationalError as e:
        if "check that column/key exists" in str(e).lower():
            print("  [SKIP] Constraint already removed")
        else:
            raise

    # Add composite unique constraint for questionlink
    try:
        cursor.execute("""
            ALTER TABLE questionlink
            ADD UNIQUE INDEX uix_vendor_new_question (vendor_id, new_question_id)
        """)
        connection.commit()
        print("  [OK] Composite constraint added to questionlink")
    except pymysql.err.OperationalError as e:
        if "Duplicate key name" in str(e):
            print("  [SKIP] Composite constraint already exists")
        else:
            raise

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)
    print("\nDatabase is now multi-tenant ready!")
    print("\nNext steps:")
    print("  1. Restart your API server")
    print("  2. All API endpoints now require vendor_id parameter")
    print("  3. Existing data is under vendor_id='DEFAULT'")
    print("  4. You can migrate DEFAULT to specific vendors:")
    print("     UPDATE responseentry SET vendor_id='VENDOR-001' WHERE vendor_id='DEFAULT';")
    print("     UPDATE questionlink SET vendor_id='VENDOR-001' WHERE vendor_id='DEFAULT';")

    cursor.close()
    connection.close()

except Exception as e:
    print(f"\n[ERROR] Migration failed: {str(e)}")
    print("\nRollback may be required. Check database state.")
    if 'connection' in locals():
        connection.rollback()
        connection.close()
    exit(1)
