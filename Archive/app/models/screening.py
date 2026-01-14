from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ScreeningState(str, enum.Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    REJECTED = "REJECTED"


class Screening(Base):
    __tablename__ = "screenings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    submitter_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    handler_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    #Film info
    film_title = Column(String(200), nullable=False, index=True)
    film_cast = Column(Text)
    film_genre = Column(String(100), index=True)
    film_duration = Column(Integer)  #se lepta
    
    #Auditorium info
    auditorium_name = Column(String(100))
    
    #Scheduling info
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    #State kai review
    state = Column(Enum(ScreeningState), default=ScreeningState.CREATED, nullable=False, index=True)
    review_score = Column(Numeric(3, 2))  #paradeigma., 9.50
    review_comments = Column(Text)
    rejection_reason = Column(Text)
    approval_notes = Column(Text)
    is_finally_submitted = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    #Relationships
    program = relationship("Program", back_populates="screenings")
    submitter = relationship("User", foreign_keys=[submitter_id], back_populates="submitted_screenings")
    handler = relationship("User", foreign_keys=[handler_id], back_populates="handled_screenings")