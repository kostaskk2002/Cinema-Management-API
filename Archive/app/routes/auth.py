from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user
from app.models.user import User, AuthToken

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Egggrafi neou user
    O logariasmos dimiourgiete os inactive
    """
    user = AuthService.register_user(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authentication kai dimiourgia token
    """
    user, token = AuthService.authenticate_user(db, login_data)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    authorization: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout tou current user
    Invalidate tou token
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header"
        )
    
    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    AuthService.logout_user(db, current_user, token)
    return None


@router.post("/force-logout/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def force_logout(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force logout enos user apo ADMIN
    """
    AuthService.force_logout_user(db, user_id, current_user)
    return None


@router.get("/validate-token")
def validate_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Elegxos an to token einai valid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header"
        )
    
    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    is_valid = AuthService.validate_token(db, token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {"valid": True, "message": "Token is valid"}