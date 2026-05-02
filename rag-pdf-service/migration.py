from database import Base, engine, create_tables
from models import User, BlacklistedToken, RefreshToken, Document
import os

DB_FILE = "app.db"

def apply_migrations():
    """
    Applies database migrations.
    For this project, we are taking a simple approach:
    If the database file exists, we delete it and recreate it.
    This is suitable for development environments but not for production.
    """
    print("Applying database migrations...")
    if os.path.exists(DB_FILE):
        print(f"Deleting existing database file: {DB_FILE}")
        os.remove(DB_FILE)
    
    print("Creating new database tables...")
    create_tables()
    print("Database migrations applied successfully.")

if __name__ == "__main__":
    apply_migrations()
