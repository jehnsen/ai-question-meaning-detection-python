"""
Create MySQL Database - Effortless-Respond API

This script creates the MySQL database if it doesn't exist.
Run this BEFORE running the main application or reset_database.py

Usage:
    python create_mysql_database.py
"""

import pymysql
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables (override system env vars)
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

def create_database():
    """Create the MySQL database if it doesn't exist."""

    print(f"\nDEBUG: DATABASE_URL = {DATABASE_URL}")

    # Parse the database URL
    # Format: mysql+pymysql://username:password@host:port/database_name
    parsed_url = urlparse(DATABASE_URL.replace("mysql+pymysql://", "mysql://"))

    username = parsed_url.username or "root"
    password = parsed_url.password or ""
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or 3306
    database_name = parsed_url.path.lstrip("/")

    print("=" * 60)
    print("MYSQL DATABASE CREATION TOOL")
    print("=" * 60)
    print(f"\nHost: {host}:{port}")
    print(f"User: {username}")
    print(f"Database: {database_name}")

    try:
        # Connect to MySQL server (without specifying database)
        print("\nConnecting to MySQL server...")
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            charset='utf8mb4'
        )

        cursor = connection.cursor()

        # Check if database exists
        cursor.execute(f"SHOW DATABASES LIKE '{database_name}'")
        result = cursor.fetchone()

        if result:
            print(f"\n[OK] Database '{database_name}' already exists.")
        else:
            # Create database
            print(f"\nCreating database '{database_name}'...")
            cursor.execute(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"[OK] Database '{database_name}' created successfully!")

        cursor.close()
        connection.close()

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run: python reset_database.py 1  (to create tables)")
        print("  2. Run: python main.py              (to start the API)")

    except pymysql.Error as e:
        print(f"\n[ERROR] MySQL Error: {e}")
        print("\nPlease check:")
        print("  - Is MySQL server running?")
        print("  - Are the credentials correct in .env file?")
        print("  - Does the user have CREATE DATABASE privilege?")
        return False

    return True

if __name__ == "__main__":
    create_database()
