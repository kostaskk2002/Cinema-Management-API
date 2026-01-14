from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User, AuthToken
from app.models.program import ProgramRole, ProgramRoleType
from app.utils.security import decode_access_token


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    #Pairnei ton current authenticated user apo to token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not authorization:
        raise credentials_exception
    
    #Pairnei to token apo to Authorization header
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception
    
    #Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if username is None or user_id is None:
        raise credentials_exception
    
    #Elegxos sto database gia to token
    db_token = db.query(AuthToken).filter(
        AuthToken.token == token,
        AuthToken.is_valid == True
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    #Elegxos an exei lixei to token
    if db_token.expires_at < datetime.utcnow():
        db_token.is_valid = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    
    #Elegxos an to token anikei ston swsto user
    if db_token.user_id != user_id:
        #KRITIΚΟ: Deactivate kai tous 2 logariasmos
        user = db.query(User).filter(User.id == user_id).first()
        token_owner = db.query(User).filter(User.id == db_token.user_id).first()
        
        if user:
            user.is_active = False
        if token_owner:
            token_owner.is_active = False
        
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token ownership violation - both accounts deactivated"
        )
    
    #Pairnei ton user
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Elegxei an o user einai active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    #Elegxei an o user einai ADMIN
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_user_program_role(
    user_id: int,
    program_id: int,
    db: Session
) -> Optional[ProgramRoleType]:
    """
    Pairnei to role enos user se ena program
    
    Returns:
        To ProgramRoleType an yparxei, alliws None
    """
    role = db.query(ProgramRole).filter(
        ProgramRole.user_id == user_id,
        ProgramRole.program_id == program_id
    ).first()
    
    return role.role if role else None


def check_program_permission(
    user: User,
    program_id: int,
    required_roles: list[ProgramRoleType],
    db: Session
) -> bool:
    """
    Elegxei an enas user exei ta aparaitita permissions se ena program
    """
    if user.role == "ADMIN":
        return False  #ADMIN den exei auto-access sta programs
    
    user_role = get_user_program_role(user.id, program_id, db)
    
    return user_role in required_roles if user_role else False