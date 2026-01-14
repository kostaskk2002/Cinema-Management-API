from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    username: str = Field(..., min_length=5, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        #Prepei na arxizei me gramma
        if not v[0].isalpha():
            raise ValueError('Username prepei na arxizei me gramma')
        
        #Mono alphanumeric kai underscore
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('Username mporei na periexei mono grammata, arithmous kai underscore')
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        #Toulaxiston 8 xaraktires
        if len(v) < 8:
            raise ValueError('Password prepei na exei toulaxiston 8 xaraktires')
        
        #Prepei na exei kefalaia
        if not any(c.isupper() for c in v):
            raise ValueError('Password prepei na periexei toulaxiston ena kefaleo gramma')
        
        #Prepei na exei peza
        if not any(c.islower() for c in v):
            raise ValueError('Password prepei na periexei toulaxiston ena pezo gramma')
        
        #Prepei na exei arithmo
        if not any(c.isdigit() for c in v):
            raise ValueError('Password prepei na periexei toulaxiston enan arithmo')
        
        #Prepei na exei special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password prepei na periexei toulaxiston ena special character')
        
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, min_length=5, max_length=50)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is None:
            return v
        
        if not v[0].isalpha():
            raise ValueError('Username prepei na arxizei me gramma')
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('Username mporei na periexei mono grammata, arithmous kai underscore')
        
        return v


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password prepei na exei toulaxiston 8 xaraktires')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password prepei na periexei toulaxiston ena kefaleo gramma')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password prepei na periexei toulaxiston ena pezo gramma')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password prepei na periexei toulaxiston enan arithmo')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password prepei na periexei toulaxiston ena special character')
        
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse