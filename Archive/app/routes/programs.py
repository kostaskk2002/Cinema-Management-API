from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.program import (
    ProgramCreate, ProgramUpdate, ProgramResponse,
    ProgramStateUpdate, ProgramRoleAdd, ProgramSearchParams,
    ProgramRoleResponse
)
from app.services.program_service import ProgramService
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.models.program import ProgramState

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(
    program_data: ProgramCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dimiourgia neou program
    O creator ginete automatically PROGRAMMER
    """
    program = ProgramService.create_program(db, program_data, current_user)
    return program


@router.get("/search", response_model=List[ProgramResponse])
def search_programs(
    name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    film_title: Optional[str] = Query(None),
    auditorium: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Anazitisi programs (xoris authentication)
    VISITOR vlepei mono ANNOUNCED programs
    """
    from datetime import datetime
    
    search_params = ProgramSearchParams(
        name=name,
        description=description,
        start_date=datetime.fromisoformat(start_date).date() if start_date else None,
        end_date=datetime.fromisoformat(end_date).date() if end_date else None,
        film_title=film_title,
        auditorium=auditorium
    )
    
    programs = ProgramService.search_programs(db, search_params, None)
    return programs


@router.get("/search/authenticated", response_model=List[ProgramResponse])
def search_programs_authenticated(
    name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    film_title: Optional[str] = Query(None),
    auditorium: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Anazitisi programs (authenticated)
    Vlepei ANNOUNCED + programs pou exei role
    """
    from datetime import datetime
    
    search_params = ProgramSearchParams(
        name=name,
        description=description,
        start_date=datetime.fromisoformat(start_date).date() if start_date else None,
        end_date=datetime.fromisoformat(end_date).date() if end_date else None,
        film_title=film_title,
        auditorium=auditorium
    )
    
    programs = ProgramService.search_programs(db, search_params, current_user)
    return programs


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: int,
    db: Session = Depends(get_db)
):
    """
    Pairnei details enos program (xoris authentication)
    VISITOR vlepei mono ANNOUNCED programs
    """
    program = ProgramService.get_program_details(db, program_id, None)
    return program


@router.get("/{program_id}/authenticated", response_model=ProgramResponse)
def get_program_authenticated(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pairnei details enos program (authenticated)
    Vlepei analoga me to role tou
    """
    program = ProgramService.get_program_details(db, program_id, current_user)
    return program


@router.put("/{program_id}", response_model=ProgramResponse)
def update_program(
    program_id: int,
    program_data: ProgramUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update program
    Mono PROGRAMMER mporei
    """
    program = ProgramService.update_program(db, program_id, program_data, current_user)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Diagrafi program
    Mono se CREATED state kai mono apo PROGRAMMER
    """
    ProgramService.delete_program(db, program_id, current_user)
    return None


@router.put("/{program_id}/state", response_model=ProgramResponse)
def update_program_state(
    program_id: int,
    state_data: ProgramStateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allagi state tou program
    Mono PROGRAMMER mporei
    """
    program = ProgramService.update_program_state(db, program_id, state_data.new_state, current_user)
    return program


@router.post("/{program_id}/programmers", response_model=ProgramRoleResponse, status_code=status.HTTP_201_CREATED)
def add_programmer(
    program_id: int,
    role_data: ProgramRoleAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prosthiki PROGRAMMER se program
    Mono existing PROGRAMMER mporei
    """
    #Validation oti to role einai PROGRAMMER
    from app.models.program import ProgramRoleType
    if role_data.role != ProgramRoleType.PROGRAMMER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for adding programmers"
        )
    
    role = ProgramService.add_programmer(db, program_id, role_data.user_id, current_user)
    return role


@router.post("/{program_id}/staff", response_model=ProgramRoleResponse, status_code=status.HTTP_201_CREATED)
def add_staff(
    program_id: int,
    role_data: ProgramRoleAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prosthiki STAFF se program
    Mono PROGRAMMER mporei
    Meta SUBMISSION, to STAFF set einai frozen
    """
    #Validation oti to role einai STAFF
    from app.models.program import ProgramRoleType
    if role_data.role != ProgramRoleType.STAFF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for adding staff"
        )
    
    role = ProgramService.add_staff(db, program_id, role_data.user_id, current_user)
    return role