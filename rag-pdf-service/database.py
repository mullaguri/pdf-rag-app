from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from config import settings

SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Filter out SQL DDL statements but keep SQL errors
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)

# Enable full Python tracebacks
import traceback
import sys

def log_exception(exc_type, value, tb):
    """Log full exception traceback."""
    if exc_type is not None:
        print(f"\n{'='*60}")
        traceback.print_exception(exc_type, value, tb)
        print(f"{'='*60}")

# Override default exception handler
sys.excepthook = log_exception


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()   
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency — used in every route to get a db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
