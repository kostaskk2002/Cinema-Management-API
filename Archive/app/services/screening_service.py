from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.models.user import User, UserRole
from app.models.program import Program, ProgramRole, ProgramState, ProgramRoleType
from app.models.screening import Screening, ScreeningState
from app.schemas.screening import (
    ScreeningCreate, ScreeningUpdate, ScreeningReview,
    ScreeningApproval, ScreeningRejection, HandlerAssignment,
    ScreeningSearchParams
)
from app.utils.dependencies import get_user_program_role
from app.services.program_service import ProgramService


class ScreeningService:
    
    @staticmethod
    def create_screening(db: Session, screening_data: ScreeningCreate, creator: User) -> Screening:
        """
        Dimiourgia neou screening
        O dimiourgos ginete automatically SUBMITTER
        """
        #Elegxos an yparxei to program
        program = ProgramService.get_program_by_id(db, screening_data.program_id)
        
        #Elegxos an o creator einai PROGRAMMER tou idiou program
        user_role = get_user_program_role(creator.id, screening_data.program_id, db)
        if user_role == ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Programmers cannot submit screenings in their own program"
            )
        
        #Dimiourgia screening
        new_screening = Screening(
            program_id=screening_data.program_id,
            submitter_id=creator.id,
            film_title=screening_data.film_title,
            film_cast=screening_data.film_cast,
            film_genre=screening_data.film_genre,
            film_duration=screening_data.film_duration,
            auditorium_name=screening_data.auditorium_name,
            start_time=screening_data.start_time,
            end_time=screening_data.end_time,
            state=ScreeningState.CREATED
        )
        
        db.add(new_screening)
        db.flush()
        
        #Prosthiki tou creator os SUBMITTER sto program (an den einai idi)
        existing_submitter_role = db.query(ProgramRole).filter(
            ProgramRole.user_id == creator.id,
            ProgramRole.program_id == screening_data.program_id,
            ProgramRole.role == ProgramRoleType.SUBMITTER
        ).first()
        
        if not existing_submitter_role:
            submitter_role = ProgramRole(
                user_id=creator.id,
                program_id=screening_data.program_id,
                role=ProgramRoleType.SUBMITTER
            )
            db.add(submitter_role)
        
        db.commit()
        db.refresh(new_screening)
        
        return new_screening
    
    
    @staticmethod
    def get_screening_by_id(db: Session, screening_id: int) -> Screening:
        """
        Pairnei screening me vasi to id
        """
        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screening not found"
            )
        return screening
    
    
    @staticmethod
    def update_screening(
        db: Session,
        screening_id: int,
        screening_data: ScreeningUpdate,
        current_user: User
    ) -> Screening:
        """
        Update screening
        Mono SUBMITTER mporei na kanei update kai mono otan einai se CREATED state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos an einai o submitter
        if screening.submitter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only submitter can update screening"
            )
        
        #Mono se CREATED state
        if screening.state != ScreeningState.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update screenings in CREATED state"
            )
        
        #Update fields
        if screening_data.film_title is not None:
            screening.film_title = screening_data.film_title
        
        if screening_data.film_cast is not None:
            screening.film_cast = screening_data.film_cast
        
        if screening_data.film_genre is not None:
            screening.film_genre = screening_data.film_genre
        
        if screening_data.film_duration is not None:
            screening.film_duration = screening_data.film_duration
        
        if screening_data.auditorium_name is not None:
            screening.auditorium_name = screening_data.auditorium_name
        
        if screening_data.start_time is not None:
            screening.start_time = screening_data.start_time
        
        if screening_data.end_time is not None:
            screening.end_time = screening_data.end_time
        
        #Elegxos oti end_time > start_time
        if screening.start_time and screening.end_time:
            if screening.end_time <= screening.start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time"
                )
            
            #Elegxos oti i diarkeia einai >= film_duration
            if screening.film_duration:
                duration_minutes = (screening.end_time - screening.start_time).total_seconds() / 60
                if duration_minutes < screening.film_duration:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Time slot duration must be >= film duration"
                    )
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def submit_screening(db: Session, screening_id: int, current_user: User) -> Screening:
        """
        Submit screening sto program
        Prepei na einai complete (film, auditorium, times)
        To program prepei na einai se SUBMISSION state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos an einai o submitter
        if screening.submitter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only submitter can submit screening"
            )
        
        #Prepei na einai se CREATED state
        if screening.state != ScreeningState.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Screening must be in CREATED state"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state != ProgramState.SUBMISSION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in SUBMISSION state"
            )
        
        #Elegxos oti einai complete
        if not all([
            screening.film_title,
            screening.film_duration,
            screening.auditorium_name,
            screening.start_time,
            screening.end_time
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Screening must be complete (film, auditorium, times required)"
            )
        
        #Allagi state
        screening.state = ScreeningState.SUBMITTED
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def withdraw_screening(db: Session, screening_id: int, current_user: User) -> None:
        """
        Withdraw kai diagrafi screening
        Mono otan einai se CREATED state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos an einai o submitter
        if screening.submitter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only submitter can withdraw screening"
            )
        
        #Mono se CREATED state
        if screening.state != ScreeningState.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only withdraw screenings in CREATED state"
            )
        
        db.delete(screening)
        db.commit()
    
    
    @staticmethod
    def assign_handler(
        db: Session,
        screening_id: int,
        handler_data: HandlerAssignment,
        current_user: User
    ) -> Screening:
        """
        Assignment STAFF handler se screening
        Mono PROGRAMMER mporei na kanei assign
        To program prepei na einai se ASSIGNMENT state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos permissions (prepei na einai PROGRAMMER)
        user_role = get_user_program_role(current_user.id, screening.program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can assign handlers"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state != ProgramState.ASSIGNMENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in ASSIGNMENT state"
            )
        
        #Elegxos oti o handler einai STAFF tou program
        handler_role = get_user_program_role(handler_data.handler_id, screening.program_id, db)
        if handler_role != ProgramRoleType.STAFF:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Handler must be staff member of this program"
            )
        
        #Assignment handler
        screening.handler_id = handler_data.handler_id
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def review_screening(
        db: Session,
        screening_id: int,
        review_data: ScreeningReview,
        current_user: User
    ) -> Screening:
        """
        Review screening apo ton assigned STAFF handler
        To program prepei na einai se REVIEW state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos an einai o assigned handler
        if screening.handler_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only assigned handler can review screening"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state != ProgramState.REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in REVIEW state"
            )
        
        #Prosthiki review
        screening.review_score = review_data.review_score
        screening.review_comments = review_data.review_comments
        screening.state = ScreeningState.REVIEWED
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def approve_screening(
        db: Session,
        screening_id: int,
        approval_data: ScreeningApproval,
        current_user: User
    ) -> Screening:
        """
        Approval screening
        Mono SUBMITTER mporei na kanei approve
        To program prepei na einai se SCHEDULING state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos an einai o submitter
        if screening.submitter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only submitter can approve screening"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state != ProgramState.SCHEDULING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in SCHEDULING state"
            )
        
        #Approval
        screening.approval_notes = approval_data.approval_notes
        screening.state = ScreeningState.APPROVED
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def reject_screening(
        db: Session,
        screening_id: int,
        rejection_data: ScreeningRejection,
        current_user: User
    ) -> Screening:
        """
        Rejection screening apo PROGRAMMER
        Mporei na ginei se SCHEDULING i DECISION state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos permissions (prepei na einai PROGRAMMER)
        user_role = get_user_program_role(current_user.id, screening.program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can reject screenings"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state not in [ProgramState.SCHEDULING, ProgramState.DECISION]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in SCHEDULING or DECISION state"
            )
        
        #Rejection
        screening.rejection_reason = rejection_data.rejection_reason
        screening.state = ScreeningState.REJECTED
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def final_submit_screening(
        db: Session,
        screening_id: int,
        current_user: User
    ) -> Screening:
        """
        Final submission tou screening me required changes
        Mono SUBMITTER mporei
        To program prepei na einai se FINAL_PUBLICATION state
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos an einai o submitter
        if screening.submitter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only submitter can final submit screening"
            )
        
        #Prepei na einai APPROVED
        if screening.state != ScreeningState.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Screening must be approved before final submission"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state != ProgramState.FINAL_PUBLICATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in FINAL_PUBLICATION state"
            )
        
        #Final submission
        screening.is_finally_submitted = True
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def accept_screening(
        db: Session,
        screening_id: int,
        current_user: User
    ) -> Screening:
        """
        Teliki apodoxi screening (SCHEDULED)
        Mono PROGRAMMER mporei
        To program prepei na einai se DECISION state
        To screening prepei na einai APPROVED kai finally submitted
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        
        #Elegxos permissions (prepei na einai PROGRAMMER)
        user_role = get_user_program_role(current_user.id, screening.program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can accept screenings"
            )
        
        #Elegxos program state
        program = ProgramService.get_program_by_id(db, screening.program_id)
        if program.state != ProgramState.DECISION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be in DECISION state"
            )
        
        #Prepei na einai APPROVED kai finally submitted
        if screening.state != ScreeningState.APPROVED or not screening.is_finally_submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Screening must be approved and finally submitted"
            )
        
        #Accept
        screening.state = ScreeningState.SCHEDULED
        
        db.commit()
        db.refresh(screening)
        return screening
    
    
    @staticmethod
    def auto_reject_non_submitted(db: Session, program_id: int) -> int:
        """
        Auto-rejection gia approved screenings pou den kanane final submit
        Kaleitai otan to program paei se DECISION state
        
        Returns:
            Arithmos rejected screenings
        """
        #Pairnei ola ta APPROVED screenings pou DEN einai finally submitted
        screenings = db.query(Screening).filter(
            Screening.program_id == program_id,
            Screening.state == ScreeningState.APPROVED,
            Screening.is_finally_submitted == False
        ).all()
        
        count = 0
        for screening in screenings:
            screening.state = ScreeningState.REJECTED
            screening.rejection_reason = "Automatic rejection - not finally submitted"
            count += 1
        
        db.commit()
        return count
    
    
    @staticmethod
    def search_screenings(
        db: Session,
        program_id: int,
        search_params: ScreeningSearchParams,
        current_user: Optional[User] = None
    ) -> List[Screening]:
        """
        Anazitisi screenings mesa se ena program
        Filtering analoga me role
        """
        query = db.query(Screening).filter(Screening.program_id == program_id)
        
        #Filters
        if search_params.film_title:
            #AND semantics: ola ta words prepei na yparxoun
            words = search_params.film_title.lower().split()
            for word in words:
                query = query.filter(Screening.film_title.ilike(f"%{word}%"))
        
        if search_params.film_cast:
            words = search_params.film_cast.lower().split()
            for word in words:
                query = query.filter(Screening.film_cast.ilike(f"%{word}%"))
        
        if search_params.film_genre:
            words = search_params.film_genre.lower().split()
            for word in words:
                query = query.filter(Screening.film_genre.ilike(f"%{word}%"))
        
        if search_params.start_date:
            query = query.filter(Screening.start_time >= search_params.start_date)
        
        if search_params.end_date:
            query = query.filter(Screening.start_time <= search_params.end_date)
        
        #Role-based filtering
        program = ProgramService.get_program_by_id(db, program_id)
        
        if not current_user:
            #VISITOR: mono SCHEDULED screenings se ANNOUNCED programs
            if program.state != ProgramState.ANNOUNCED:
                return []
            query = query.filter(Screening.state == ScreeningState.SCHEDULED)
        else:
            user_role = get_user_program_role(current_user.id, program_id, db)
            
            if user_role == ProgramRoleType.PROGRAMMER:
                #PROGRAMMER vlepei ola
                pass
            elif user_role == ProgramRoleType.STAFF:
                #STAFF vlepei mono osa einai assigned se auton
                query = query.filter(Screening.handler_id == current_user.id)
            elif user_role == ProgramRoleType.SUBMITTER:
                #SUBMITTER vlepei mono ta dika tou
                query = query.filter(Screening.submitter_id == current_user.id)
            else:
                #Simple USER: mono SCHEDULED se ANNOUNCED programs
                if program.state != ProgramState.ANNOUNCED:
                    return []
                query = query.filter(Screening.state == ScreeningState.SCHEDULED)
        
        #Sorting: film_genre, meta film_title
        results = query.order_by(Screening.film_genre, Screening.film_title).all()
        
        return results
    
    
    @staticmethod
    def get_screening_details(
        db: Session,
        screening_id: int,
        current_user: Optional[User] = None
    ) -> Screening:
        """
        Pairnei details enos screening
        Access control analoga me role
        """
        screening = ScreeningService.get_screening_by_id(db, screening_id)
        program = ProgramService.get_program_by_id(db, screening.program_id)
        
        #Access control
        if not current_user:
            #VISITOR: mono SCHEDULED se ANNOUNCED programs
            if program.state != ProgramState.ANNOUNCED or screening.state != ScreeningState.SCHEDULED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Screening not accessible"
                )
        else:
            user_role = get_user_program_role(current_user.id, screening.program_id, db)
            
            if user_role == ProgramRoleType.PROGRAMMER:
                #PROGRAMMER vlepei ola
                pass
            elif user_role == ProgramRoleType.STAFF:
                #STAFF vlepei mono osa einai assigned se auton
                if screening.handler_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to view this screening"
                    )
            elif user_role == ProgramRoleType.SUBMITTER:
                #SUBMITTER vlepei mono ta dika tou
                if screening.submitter_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to view this screening"
                    )
            else:
                #Simple USER: mono SCHEDULED se ANNOUNCED programs
                if program.state != ProgramState.ANNOUNCED or screening.state != ScreeningState.SCHEDULED:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Screening not accessible"
                    )
        
        return screening