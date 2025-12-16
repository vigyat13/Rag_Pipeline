from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# FIX: Render provides 'postgres://' but SQLAlchemy requires 'postgresql://'
# ---------------------------------------------------------------------------
sqlalchemy_database_url = settings.DATABASE_URL

if sqlalchemy_database_url and sqlalchemy_database_url.startswith("postgres://"):
    sqlalchemy_database_url = sqlalchemy_database_url.replace("postgres://", "postgresql://", 1)

# Handle SQLite vs Postgres
if sqlalchemy_database_url.startswith("sqlite"):
    engine = create_engine(
        sqlalchemy_database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
else:
    # For PostgreSQL (and others)
    engine = create_engine(sqlalchemy_database_url, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
