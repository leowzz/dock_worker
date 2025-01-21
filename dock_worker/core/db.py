from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dock_worker.core import config

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{config.db_path}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


# Create base class for declarative models
class Base(DeclarativeBase):
    pass


@contextmanager
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
    run_id = Column(String, index=True)
    distinct_id = Column(String, index=True)
    status = Column(String, comment="状态: completed, in_progress, failed, pending")
    repo_url = Column(String, index=True)
    repo_namespace = Column(String, index=True)
    workflow_id = Column(Integer, index=True)
    workflow_name = Column(String, index=True)
    full_url = Column(String, index=True)


def init_db():
    """
    Initialize database
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
