from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, declarative_base

# Check local file located file
SQLALCHEMY_DATABASE_URL = "sqlite:///./sprout.db"

# Connect to SQLite DB
engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
        )

# Create sesion
SessionLocal = sessionmaker(autocommit=False, autoflush = False, bind=engine)

# Base class for ORM Models to map Python Classes into database tables
Base = declarative_base()

def get_db():
    """
    Creates and yields a database session.

    Ensure the session is closed after request finishes.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
