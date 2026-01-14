from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.user import User, AuthToken, UserRole
from app.schemas.user import UserUpdate, PasswordUpdate
from app.utils.security import verify_password, get_password_hash
from app.utils.validators import validate_username, validate_password


class UserService:
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """
        Pairnei user me vasi to id
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Pairnei user me vasi to username
        """
        return db.query(User).filter(User.username == username).first()
    
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Pairnei ola ta users (gia ADMIN)
        """
        return db.query(User).offset(skip).limit(limit).all()
    
    
    @staticmethod
    def update_user_info(
        db: Session, 
        user_id: int, 
        user_data: UserUpdate, 
        current_user: User
    ) -> User:
        """
        Update user information (full_name, email, username)
        Epitrepete mono apo ton idio ton user i apo ADMIN
        """
        #Pairnei ton user pros update
        user = UserService.get_user_by_id(db, user_id)
        
        #Elegxos permissions (mono o idios i ADMIN)
        if current_user.id != user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
        
        #Update full_name
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        #Update email
        if user_data.email is not None:
            user.email = user_data.email
        
        #Update username (kai invalidate token an allaxei)
        if user_data.username is not None and user_data.username != user.username:
            #Validation
            is_valid, error_msg = validate_username(user_data.username)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            #Elegxos an yparxei to neo username
            existing = db.query(User).filter(User.username == user_data.username).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            user.username = user_data.username
            
            #Invalidate current token
            db.query(AuthToken).filter(
                AuthToken.user_id == user.id,
                AuthToken.is_valid == True
            ).update({"is_valid": False})
        
        db.commit()
        db.refresh(user)
        return user
    
    
    @staticmethod
    def update_password(
        db: Session,
        user_id: int,
        password_data: PasswordUpdate,
        current_user: User
    ) -> None:
        """
        Allagi password
        Meta apo 3 failed attempts, deactivate account
        """
        #Pairnei ton user
        user = UserService.get_user_by_id(db, user_id)
        
        #Mono o idios o user mporei na allaxei to password tou
        if current_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change this password"
            )
        
        #Elegxos oti ta 2 nea passwords tairiazoun
        if password_data.new_password != password_data.new_password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )
        
        #Elegxos tou paliou password
        if not verify_password(password_data.old_password, user.password_hash):
            #Auxisi failed attempts
            user.failed_login_attempts += 1
            
            #An exei 3 failed attempts, deactivate
            if user.failed_login_attempts >= 3:
                user.is_active = False
                
                #Invalidate ola ta tokens
                db.query(AuthToken).filter(
                    AuthToken.user_id == user.id,
                    AuthToken.is_valid == True
                ).update({"is_valid": False})
                
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account deactivated due to multiple failed password attempts"
                )
            
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect old password"
            )
        
        #Validation neou password
        is_valid, error_msg = validate_password(password_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        #Update password
        user.password_hash = get_password_hash(password_data.new_password)
        user.failed_login_attempts = 0
        
        #Invalidate ola ta tokens
        db.query(AuthToken).filter(
            AuthToken.user_id == user.id,
            AuthToken.is_valid == True
        ).update({"is_valid": False})
        
        db.commit()
    
    
    @staticmethod
    def update_account_status(
        db: Session,
        user_id: int,
        is_active: bool,
        admin_user: User
    ) -> User:
        """
        Activate/Deactivate account (mono ADMIN)
        """
        #Elegxos oti einai ADMIN
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        #Pairnei ton user
        user = UserService.get_user_by_id(db, user_id)
        
        #Update status
        user.is_active = is_active
        
        #An deactivate, invalidate ola ta tokens
        if not is_active:
            db.query(AuthToken).filter(
                AuthToken.user_id == user.id,
                AuthToken.is_valid == True
            ).update({"is_valid": False})
        
        db.commit()
        db.refresh(user)
        return user
    
    
    @staticmethod
    def delete_user(
        db: Session,
        user_id: int,
        current_user: User
    ) -> None:
        """
        Diagrafi user
        Epitrepete apo ADMIN i apo ton idio ton user (self-delete)
        ADMIN accounts den mporoun na diagrafoun
        """
        #Pairnei ton user pros diagrafi
        user = UserService.get_user_by_id(db, user_id)
        
        #Elegxos an o user pros diagrafi einai ADMIN
        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete admin accounts"
            )
        
        #Elegxos permissions
        if current_user.id != user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user"
            )
        
        #Diagrafi (ta tokens tha diagrafoun automatically logo cascade)
        db.delete(user)
        db.commit()