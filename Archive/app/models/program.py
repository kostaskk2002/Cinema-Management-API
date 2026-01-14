from sqlalchemy import Column, Integer, String, Text, Date, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ProgramState(str, enum.Enum):
    CREATED = "CREATED"
    SUBMISSION = "SUBMISSION"
    ASSIGNMENT = "ASSIGNMENT"
    REVIEW = "REVIEW"
    SCHEDULING = "SCHEDULING"
    FINAL_PUBLICATION = "FINAL_PUBLICATION"
    DECISION = "DECISION"
    ANNOUNCED = "ANNOUNCED"


class ProgramRoleType(str, enum.Enum):
    PROGRAMMER = "PROGRAMMER"
    STAFF = "STAFF"
    SUBMITTER = "SUBMITTER"


class Program(Base):
    __tablename__ = "programs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    state = Column(Enum(ProgramState), default=ProgramState.CREATED, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    #Relationships
    program_roles = relationship("ProgramRole", back_populates="program", cascade="all, delete-orphan")
    screenings = relationship("Screening", back_populates="program", cascade="all, delete-orphan")


class ProgramRole(Base):
    __tablename__ = "program_roles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(ProgramRoleType), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    #Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'program_id', 'role', name='unique_user_program_role'),
    )
    
    #Relationships
    user = relationship("User", back_populates="program_roles")
    program = relationship("Program", back_populates="program_roles")