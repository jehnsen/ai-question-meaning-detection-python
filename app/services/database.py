"""
Database connection and session management.
"""
import os
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/effortless_respond")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """
    Initialize database: create all tables.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency for database session.

    Yields:
        Session: SQLModel database session
    """
    with Session(engine) as session:
        yield session
