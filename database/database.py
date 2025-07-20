"""
Database configuration and connection management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from config.settings import get_settings

settings = get_settings()

# Create database engine
if settings.database_url_sync.startswith("sqlite"):
    engine = create_engine(
        settings.database_url_sync,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    engine = create_engine(
        settings.database_url_sync,
        pool_size=20,
        max_overflow=30,
        echo=settings.debug
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    """
    import database.models  # Import all models
    Base.metadata.create_all(bind=engine)


def reset_db():
    """
    Reset database (drop and recreate all tables).
    WARNING: This will delete all data!
    """
    import database.models  # Import all models
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)