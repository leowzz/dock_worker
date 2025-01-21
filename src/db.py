from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.db_path}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()


def get_db():
    """
    Get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Jobs(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    source = Column(String, index=True)
    target = Column(String, index=True)
    run_number = Column(Integer, index=True)
    status = Column(String, comment="状态: completed, running, failed, pending")
    repo_url = Column(String, index=True)
    repo_namespace = Column(String, index=True)


def init_db():
    """
    Initialize database
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
