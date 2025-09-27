from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"), index=True)
    question_type = Column(String)  # mcq / match / desc
    question_text = Column(String)
    options = Column(JSON, nullable=True)
    answer = Column(String, nullable=True)
    question_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "type": self.question_type,
            "question_text": self.question_text,
            "options": self.options,
            "answer": self.answer,
            "metadata": self.question_metadata
        }
