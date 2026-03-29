from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency do FastAPI.
    Abre uma session no inicio do request e garante o close no finally,
    mesmo se rolar exception no meio do caminho.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
