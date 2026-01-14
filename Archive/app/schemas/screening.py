from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.screening import ScreeningState


class ScreeningCreate(BaseModel):
    program_id: int
    film_title: str = Field(..., min_length=1, max_length=200)
    film_cast: Optional[str] = None
    film_genre: Optional[str] = Field(None, max_length=100)
    film_duration: Optional[int] = Field(None, gt=0)  #se lepta
    auditorium_name: Optional[str] = Field(None, max_length=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ScreeningUpdate(BaseModel):
    film_title: Optional[str] = Field(None, min_length=1, max_length=200)
    film_cast: Optional[str] = None
    film_genre: Optional[str] = Field(None, max_length=100)
    film_duration: Optional[int] = Field(None, gt=0)
    auditorium_name: Optional[str] = Field(None, max_length=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @field_validator('end_time')
    @classmethod
    def validate_times(cls, v, info):
        if v and 'start_time' in info.data and info.data['start_time']:
            if v <= info.data['start_time']:
                raise ValueError('End time prepei na einai meta apo start time')
        return v


class ScreeningReview(BaseModel):
    review_score: Decimal = Field(..., ge=0, le=10)
    review_comments: str = Field(..., min_length=1)


class ScreeningApproval(BaseModel):
    approval_notes: Optional[str] = None


class ScreeningRejection(BaseModel):
    rejection_reason: str = Field(..., min_length=1)


class HandlerAssignment(BaseModel):
    handler_id: int


class ScreeningResponse(BaseModel):
    id: int
    program_id: int
    submitter_id: int
    handler_id: Optional[int]
    film_title: str
    film_cast: Optional[str]
    film_genre: Optional[str]
    film_duration: Optional[int]
    auditorium_name: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    state: str
    review_score: Optional[Decimal]
    review_comments: Optional[str]
    rejection_reason: Optional[str]
    approval_notes: Optional[str]
    is_finally_submitted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScreeningSearchParams(BaseModel):
    film_title: Optional[str] = None
    film_cast: Optional[str] = None
    film_genre: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None