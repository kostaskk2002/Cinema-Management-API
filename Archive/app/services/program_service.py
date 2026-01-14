from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date

from app.models.user import User, UserRole
from app.models.program import Program, ProgramRole, ProgramState, ProgramRoleType
from app.schemas.program import ProgramCreate, ProgramUpdate, ProgramSearchParams
from app.utils.dependencies import get_user_program_role


class ProgramService:
    
    @staticmethod
    def create_program(db: Session, program_data: ProgramCreate, creator: User) -> Program:
        """
        Dimiourgia neou program
        O dimiourgos ginete automatically PROGRAMMER
        """
        #Elegxos an yparxei to onoma
        existing = db.query(Program).filter(Program.name == program_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program name already exists"
            )
        
        #Elegxos imerominion
        if program_data.end_date < program_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        #Dimiourgia program
        new_program = Program(
            name=program_data.name,
            description=program_data.description,
            start_date=program_data.start_date,
            end_date=program_data.end_date,
            state=ProgramState.CREATED
        )
        
        db.add(new_program)
        db.flush()  #gia na paroume to id
        
        #Prosthiki tou creator os PROGRAMMER
        creator_role = ProgramRole(
            user_id=creator.id,
            program_id=new_program.id,
            role=ProgramRoleType.PROGRAMMER
        )
        
        db.add(creator_role)
        db.commit()
        db.refresh(new_program)
        
        return new_program
    
    
    @staticmethod
    def get_program_by_id(db: Session, program_id: int) -> Program:
        """
        Pairnei program me vasi to id
        """
        program = db.query(Program).filter(Program.id == program_id).first()
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        return program
    
    
    @staticmethod
    def update_program(
        db: Session,
        program_id: int,
        program_data: ProgramUpdate,
        current_user: User
    ) -> Program:
        """
        Update program info
        Mono PROGRAMMER tou program mporei na kanei update
        Den epitrepete meta to ANNOUNCED state
        """
        program = ProgramService.get_program_by_id(db, program_id)
        
        #Elegxos permissions (prepei na einai PROGRAMMER)
        user_role = get_user_program_role(current_user.id, program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can update program"
            )
        
        #Den epitrepete update meta to ANNOUNCED
        if program.state == ProgramState.ANNOUNCED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update program in ANNOUNCED state"
            )
        
        #Update fields
        if program_data.name is not None:
            #Elegxos an yparxei allo program me to idio onoma
            existing = db.query(Program).filter(
                Program.name == program_data.name,
                Program.id != program_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Program name already exists"
                )
            program.name = program_data.name
        
        if program_data.description is not None:
            program.description = program_data.description
        
        if program_data.start_date is not None:
            program.start_date = program_data.start_date
        
        if program_data.end_date is not None:
            program.end_date = program_data.end_date
        
        #Elegxos imerominion
        if program.end_date < program.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        db.commit()
        db.refresh(program)
        return program
    
    
    @staticmethod
    def delete_program(db: Session, program_id: int, current_user: User) -> None:
        """
        Diagrafi program
        Mono an einai se CREATED state kai mono apo PROGRAMMER
        """
        program = ProgramService.get_program_by_id(db, program_id)
        
        #Elegxos permissions
        user_role = get_user_program_role(current_user.id, program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can delete program"
            )
        
        #Mono se CREATED state
        if program.state != ProgramState.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only delete programs in CREATED state"
            )
        
        db.delete(program)
        db.commit()
    
    
    @staticmethod
    def update_program_state(
        db: Session,
        program_id: int,
        new_state: ProgramState,
        current_user: User
    ) -> Program:
        """
        Allagi state tou program
        Mono PROGRAMMER mporei na allaxei state
        Ta states prepei na akolouthoun tin sosta seira
        """
        program = ProgramService.get_program_by_id(db, program_id)
        
        #Elegxos permissions
        user_role = get_user_program_role(current_user.id, program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can update program state"
            )
        
        #Elegxos valid transitions
        valid_transitions = {
            ProgramState.CREATED: [ProgramState.SUBMISSION],
            ProgramState.SUBMISSION: [ProgramState.ASSIGNMENT],
            ProgramState.ASSIGNMENT: [ProgramState.REVIEW],
            ProgramState.REVIEW: [ProgramState.SCHEDULING],
            ProgramState.SCHEDULING: [ProgramState.FINAL_PUBLICATION],
            ProgramState.FINAL_PUBLICATION: [ProgramState.DECISION],
            ProgramState.DECISION: [ProgramState.ANNOUNCED],
            ProgramState.ANNOUNCED: []  #teliko state
        }
        
        if new_state not in valid_transitions.get(program.state, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition from {program.state} to {new_state}"
            )
        
        program.state = new_state
        db.commit()
        db.refresh(program)
        
        return program
    
    
    @staticmethod
    def add_programmer(
        db: Session,
        program_id: int,
        user_id: int,
        current_user: User
    ) -> ProgramRole:
        """
        Prosthiki PROGRAMMER se program
        Mono PROGRAMMER mporei na prosthesei allous
        """
        program = ProgramService.get_program_by_id(db, program_id)
        
        #Elegxos permissions
        user_role = get_user_program_role(current_user.id, program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can add other programmers"
            )
        
        #Elegxos an yparxei o user
        from app.services.user_service import UserService
        target_user = UserService.get_user_by_id(db, user_id)
        
        #Elegxos an einai idi PROGRAMMER
        existing_role = db.query(ProgramRole).filter(
            ProgramRole.user_id == user_id,
            ProgramRole.program_id == program_id,
            ProgramRole.role == ProgramRoleType.PROGRAMMER
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a programmer for this program"
            )
        
        #Dimiourgia role
        new_role = ProgramRole(
            user_id=user_id,
            program_id=program_id,
            role=ProgramRoleType.PROGRAMMER
        )
        
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        return new_role
    
    
    @staticmethod
    def add_staff(
        db: Session,
        program_id: int,
        user_id: int,
        current_user: User
    ) -> ProgramRole:
        """
        Prosthiki STAFF se program
        Mono PROGRAMMER mporei na prosthesei STAFF
        Meta to SUBMISSION state, to STAFF set einai frozen
        """
        program = ProgramService.get_program_by_id(db, program_id)
        
        #Elegxos permissions
        user_role = get_user_program_role(current_user.id, program_id, db)
        if user_role != ProgramRoleType.PROGRAMMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only programmers can add staff"
            )
        
        #Meta to SUBMISSION, to STAFF set einai frozen
        if program.state not in [ProgramState.CREATED, ProgramState.SUBMISSION]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add staff after SUBMISSION state"
            )
        
        #Elegxos an yparxei o user
        from app.services.user_service import UserService
        target_user = UserService.get_user_by_id(db, user_id)
        
        #Elegxos an einai idi STAFF
        existing_role = db.query(ProgramRole).filter(
            ProgramRole.user_id == user_id,
            ProgramRole.program_id == program_id,
            ProgramRole.role == ProgramRoleType.STAFF
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already staff for this program"
            )
        
        #Dimiourgia role
        new_role = ProgramRole(
            user_id=user_id,
            program_id=program_id,
            role=ProgramRoleType.STAFF
        )
        
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        return new_role
    
    
    @staticmethod
    def search_programs(
        db: Session,
        search_params: ProgramSearchParams,
        current_user: Optional[User] = None
    ) -> List[Program]:
        """
        Anazitisi programs me filters
        Ta results filtraronte analoga me to user role
        """
        query = db.query(Program)
        
        #Filters
        if search_params.name:
            query = query.filter(Program.name.ilike(f"%{search_params.name}%"))
        
        if search_params.description:
            query = query.filter(Program.description.ilike(f"%{search_params.description}%"))
        
        if search_params.start_date:
            query = query.filter(Program.start_date >= search_params.start_date)
        
        if search_params.end_date:
            query = query.filter(Program.end_date <= search_params.end_date)
        
        #Film title filter (prepei na psaxei sta screenings)
        if search_params.film_title:
            from app.models.screening import Screening
            query = query.join(Screening).filter(
                Screening.film_title.ilike(f"%{search_params.film_title}%")
            ).distinct()
        
        #Auditorium filter
        if search_params.auditorium:
            from app.models.screening import Screening
            query = query.join(Screening).filter(
                Screening.auditorium_name.ilike(f"%{search_params.auditorium}%")
            ).distinct()
        
        #Role-based filtering
        if not current_user:
            #VISITOR: mono ANNOUNCED programs
            query = query.filter(Program.state == ProgramState.ANNOUNCED)
        else:
            #Authenticated users: vlepoun programs analoga me to role tous
            if current_user.role != UserRole.ADMIN:
                #Pairnei ta program IDs pou exei role o user
                user_program_ids = db.query(ProgramRole.program_id).filter(
                    ProgramRole.user_id == current_user.id
                ).all()
                user_program_ids = [pid[0] for pid in user_program_ids]
                
                #Vlepei: (a) ANNOUNCED programs KAI (b) programs pou exei role
                query = query.filter(
                    or_(
                        Program.state == ProgramState.ANNOUNCED,
                        Program.id.in_(user_program_ids)
                    )
                )
        
        #Sorting: prota me date, meta me name
        results = query.order_by(Program.start_date, Program.name).all()
        
        return results
    
    
    @staticmethod
    def get_program_details(
        db: Session,
        program_id: int,
        current_user: Optional[User] = None
    ) -> Program:
        """
        Pairnei details enos program
        Ta fields pou vlepei o user exartonte apo to role tou
        """
        program = ProgramService.get_program_by_id(db, program_id)
        
        #Elegxos access rights
        if not current_user:
            #VISITOR: mono ANNOUNCED programs
            if program.state != ProgramState.ANNOUNCED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Program not accessible"
                )
        else:
            #Authenticated users
            if current_user.role != UserRole.ADMIN:
                user_role = get_user_program_role(current_user.id, program_id, db)
                
                #An den einai ANNOUNCED kai den exei role, den to vlepei
                if program.state != ProgramState.ANNOUNCED and not user_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Program not accessible"
                    )
        
        return program