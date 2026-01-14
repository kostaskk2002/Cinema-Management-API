from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from app.models.program import ProgramState, ProgramRoleType


class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('End date prepei na einai meta apo tin start date')
        return v


class ProgramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProgramStateUpdate(BaseModel):
    new_state: ProgramState


class ProgramRoleAdd(BaseModel):
    user_id: int
    role: ProgramRoleType


class ProgramRoleResponse(BaseModel):
    id: int
    user_id: int
    role: str
    assigned_at: datetime
    
    class Config:
        from_attributes = True


class ProgramResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_date: date
    end_date: date
    state: str
    created_at: datetime
    program_roles: Optional[List[ProgramRoleResponse]] = []
    
    class Config:
        from_attributes = True


class ProgramSearchParams(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    film_title: Optional[str] = None
    auditorium: Optional[str] = None