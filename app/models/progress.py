from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"), primary_key=True)
    answered_question_ids = Column(JSON, default=[])
    score = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
