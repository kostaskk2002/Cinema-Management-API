from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.screening import (
    ScreeningCreate, ScreeningUpdate, ScreeningResponse,
    ScreeningReview, ScreeningApproval, ScreeningRejection,
    HandlerAssignment, ScreeningSearchParams
)
from app.services.screening_service import ScreeningService
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/screenings", tags=["Screenings"])


@router.post("/", response_model=ScreeningResponse, status_code=status.HTTP_201_CREATED)
def create_screening(
    screening_data: ScreeningCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dimiourgia neou screening
    O creator ginete automatically SUBMITTER
    """
    screening = ScreeningService.create_screening(db, screening_data, current_user)
    return screening


@router.get("/program/{program_id}/search", response_model=List[ScreeningResponse])
def search_screenings(
    program_id: int,
    film_title: Optional[str] = Query(None),
    film_cast: Optional[str] = Query(None),
    film_genre: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Anazitisi screenings mesa se ena program (xoris authentication)
    VISITOR vlepei mono SCHEDULED se ANNOUNCED programs
    """
    from datetime import datetime
    
    search_params = ScreeningSearchParams(
        film_title=film_title,
        film_cast=film_cast,
        film_genre=film_genre,
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None
    )
    
    screenings = ScreeningService.search_screenings(db, program_id, search_params, None)
    return screenings


@router.get("/program/{program_id}/search/authenticated", response_model=List[ScreeningResponse])
def search_screenings_authenticated(
    program_id: int,
    film_title: Optional[str] = Query(None),
    film_cast: Optional[str] = Query(None),
    film_genre: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Anazitisi screenings mesa se ena program (authenticated)
    Filtering analoga me role
    """
    from datetime import datetime
    
    search_params = ScreeningSearchParams(
        film_title=film_title,
        film_cast=film_cast,
        film_genre=film_genre,
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None
    )
    
    screenings = ScreeningService.search_screenings(db, program_id, search_params, current_user)
    return screenings


@router.get("/{screening_id}", response_model=ScreeningResponse)
def get_screening(
    screening_id: int,
    db: Session = Depends(get_db)
):
    """
    Pairnei details enos screening (xoris authentication)
    VISITOR vlepei mono SCHEDULED se ANNOUNCED programs
    """
    screening = ScreeningService.get_screening_details(db, screening_id, None)
    return screening


@router.get("/{screening_id}/authenticated", response_model=ScreeningResponse)
def get_screening_authenticated(
    screening_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pairnei details enos screening (authenticated)
    Access control analoga me role
    """
    screening = ScreeningService.get_screening_details(db, screening_id, current_user)
    return screening


@router.put("/{screening_id}", response_model=ScreeningResponse)
def update_screening(
    screening_id: int,
    screening_data: ScreeningUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update screening
    Mono SUBMITTER kai mono se CREATED state
    """
    screening = ScreeningService.update_screening(db, screening_id, screening_data, current_user)
    return screening


@router.post("/{screening_id}/submit", response_model=ScreeningResponse)
def submit_screening(
    screening_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit screening sto program
    Prepei na einai complete kai to program se SUBMISSION state
    """
    screening = ScreeningService.submit_screening(db, screening_id, current_user)
    return screening


@router.delete("/{screening_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_screening(
    screening_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Withdraw kai diagrafi screening
    Mono se CREATED state
    """
    ScreeningService.withdraw_screening(db, screening_id, current_user)
    return None


@router.put("/{screening_id}/assign-handler", response_model=ScreeningResponse)
def assign_handler(
    screening_id: int,
    handler_data: HandlerAssignment,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assignment STAFF handler se screening
    Mono PROGRAMMER kai mono se ASSIGNMENT state
    """
    screening = ScreeningService.assign_handler(db, screening_id, handler_data, current_user)
    return screening


@router.post("/{screening_id}/review", response_model=ScreeningResponse)
def review_screening(
    screening_id: int,
    review_data: ScreeningReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Review screening
    Mono o assigned STAFF handler kai mono se REVIEW state
    """
    screening = ScreeningService.review_screening(db, screening_id, review_data, current_user)
    return screening


@router.post("/{screening_id}/approve", response_model=ScreeningResponse)
def approve_screening(
    screening_id: int,
    approval_data: ScreeningApproval,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approval screening
    Mono SUBMITTER kai mono se SCHEDULING state
    """
    screening = ScreeningService.approve_screening(db, screening_id, approval_data, current_user)
    return screening


@router.post("/{screening_id}/reject", response_model=ScreeningResponse)
def reject_screening(
    screening_id: int,
    rejection_data: ScreeningRejection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rejection screening
    Mono PROGRAMMER se SCHEDULING i DECISION state
    """
    screening = ScreeningService.reject_screening(db, screening_id, rejection_data, current_user)
    return screening


@router.post("/{screening_id}/final-submit", response_model=ScreeningResponse)
def final_submit_screening(
    screening_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Final submission tou screening
    Mono SUBMITTER kai mono se FINAL_PUBLICATION state
    """
    screening = ScreeningService.final_submit_screening(db, screening_id, current_user)
    return screening


@router.post("/{screening_id}/accept", response_model=ScreeningResponse)
def accept_screening(
    screening_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Teliki apodoxi screening (SCHEDULED)
    Mono PROGRAMMER kai mono se DECISION state
    Prepei na einai APPROVED kai finally submitted
    """
    screening = ScreeningService.accept_screening(db, screening_id, current_user)
    return screening


@router.post("/program/{program_id}/auto-reject", status_code=status.HTTP_200_OK)
def auto_reject_non_submitted(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Auto-rejection gia approved screenings pou den kanane final submit
    Kaleitai otan to program paei se DECISION state
    Mono PROGRAMMER mporei na to kalei
    """
    from app.utils.dependencies import get_user_program_role
    from app.models.program import ProgramRoleType
    
    #Elegxos permissions
    user_role = get_user_program_role(current_user.id, program_id, db)
    if user_role != ProgramRoleType.PROGRAMMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only programmers can trigger auto-rejection"
        )
    
    count = ScreeningService.auto_reject_non_submitted(db, program_id)
    
    return {
        "message": f"Auto-rejected {count} screenings",
        "count": count
    }