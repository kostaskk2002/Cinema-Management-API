from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, PasswordUpdate
from app.services.user_service import UserService
from app.utils.dependencies import get_current_user, get_admin_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Pairnei ta stoixeia tou current user
    """
    return current_user


@router.get("/", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Pairnei ola ta users (mono gia ADMIN)
    """
    users = UserService.get_all_users(db, skip, limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Pairnei user me vasi to id (mono gia ADMIN)
    """
    user = UserService.get_user_by_id(db, user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user info
    Epitrepete apo ton idio ton user i apo ADMIN
    """
    user = UserService.update_user_info(db, user_id, user_data, current_user)
    return user


@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    user_id: int,
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allagi password
    Mono o idios o user mporei na allaxei to password tou
    """
    UserService.update_password(db, user_id, password_data, current_user)
    return None


@router.put("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Energopoiisi user account (mono ADMIN)
    """
    user = UserService.update_account_status(db, user_id, True, admin_user)
    return user


@router.put("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Apenergopoiisi user account (mono ADMIN)
    """
    user = UserService.update_account_status(db, user_id, False, admin_user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Diagrafi user
    Epitrepete apo ADMIN i apo ton idio ton user
    ADMIN accounts den mporoun na diagrafoun
    """
    UserService.delete_user(db, user_id, current_user)
    return None