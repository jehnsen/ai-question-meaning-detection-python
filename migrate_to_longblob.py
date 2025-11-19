"""
Migration script to update embedding column from VARBINARY to LONGBLOB.

This fixes the "Data too long for column 'embedding'" error by using
a larger column type that can handle the JSON-encoded embedding vectors.
"""
from app.services.database import engine
from sqlalchemy import text


def migrate_embedding_column():
    """
    Migrate the embedding column to LONGBLOB.

    This will:
    1. Check if responseentry table exists
    2. Alter the embedding column to LONGBLOB
    """
    print("Starting migration: embedding column to LONGBLOB...")

    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()

        try:
            # Check if table exists
            result = connection.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'responseentry'
            """))

            table_exists = result.scalar() > 0

            if table_exists:
                print("Table 'responseentry' found. Altering embedding column...")

                # Alter the embedding column to LONGBLOB
                connection.execute(text("""
                    ALTER TABLE responseentry
                    MODIFY COLUMN embedding LONGBLOB
                """))

                print("✓ Successfully altered embedding column to LONGBLOB")
            else:
                print("Table 'responseentry' does not exist. No migration needed.")
                print("Run init_db() to create tables with correct types.")

            # Commit transaction
            trans.commit()
            print("Migration completed successfully!")

        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"✗ Migration failed: {e}")
            raise


if __name__ == "__main__":
    migrate_embedding_column()
