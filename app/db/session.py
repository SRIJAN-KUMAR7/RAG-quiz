from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from sqlalchemy.orm import declarative_base

engine = create_engine(
    settings.database_url, 
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
