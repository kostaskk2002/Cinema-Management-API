from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.user import User, AuthToken, UserRole
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import verify_password, get_password_hash, generate_token_for_user
from app.utils.validators import validate_username, validate_password


class AuthService:
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """
        Dimiourgia neou user (xoris na ton energopoiei)
        """
        #Elegxos an yparxei to username
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        #Validation username kai password (ta pydantic schemas kanoun kai auto, alla gia sigoureia)
        is_valid_username, username_error = validate_username(user_data.username)
        if not is_valid_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=username_error
            )
        
        is_valid_password, password_error = validate_password(user_data.password)
        if not is_valid_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_error
            )
        
        #Hash password
        hashed_password = get_password_hash(user_data.password)
        
        #Dimiourgia user (inactive by default)
        new_user = User(
            username=user_data.username,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            email=user_data.email,
            role=UserRole.USER,
            is_active=False  #O admin prepei na ton energopoiisei
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    
    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> tuple[User, str]:
        """
        Authentication tou user kai dimiourgia token
        
        Returns:
            Tuple (user, token)
        """
        #Pairnei ton user
        user = db.query(User).filter(User.username == login_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        #Elegxos password
        if not verify_password(login_data.password, user.password_hash):
            #Auxisi failed attempts
            user.failed_login_attempts += 1
            
            #An exei 3 failed attempts, deactivate
            if user.failed_login_attempts >= 3:
                user.is_active = False
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account deactivated due to multiple failed login attempts"
                )
            
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        #Elegxos an einai active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        #Reset failed attempts
        user.failed_login_attempts = 0
        
        #Invalidate ola ta palia tokens
        db.query(AuthToken).filter(
            AuthToken.user_id == user.id,
            AuthToken.is_valid == True
        ).update({"is_valid": False})
        
        #Dimiourgia neou token
        token, expire_time = generate_token_for_user(user.id, user.username)
        
        #Apothikeusi token sti vasi
        new_token = AuthToken(
            user_id=user.id,
            token=token,
            expires_at=expire_time,
            is_valid=True
        )
        
        db.add(new_token)
        db.commit()
        db.refresh(user)
        
        return user, token
    
    
    @staticmethod
    def logout_user(db: Session, user: User, token: str) -> None:
        """
        Logout user kai invalidate token
        """
        #Invalidate to token
        db.query(AuthToken).filter(
            AuthToken.token == token,
            AuthToken.user_id == user.id
        ).update({"is_valid": False})
        
        db.commit()
    
    
    @staticmethod
    def force_logout_user(db: Session, target_user_id: int, admin_user: User) -> None:
        """
        Force logout apo ADMIN
        """
        #Elegxos oti einai ADMIN
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        #Pairnei ton target user
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        #Den epitrepete force logout se ADMIN
        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot force logout admin users"
            )
        
        #Invalidate ola ta tokens tou target user
        db.query(AuthToken).filter(
            AuthToken.user_id == target_user_id,
            AuthToken.is_valid == True
        ).update({"is_valid": False})
        
        db.commit()
    
    
    @staticmethod
    def validate_token(db: Session, token: str) -> bool:
        #Elegxos an to token einai valid
        db_token = db.query(AuthToken).filter(
            AuthToken.token == token,
            AuthToken.is_valid == True
        ).first()
        
        if not db_token:
            return False
        
        #Elegxos expiration
        if db_token.expires_at < datetime.utcnow():
            db_token.is_valid = False
            db.commit()
            return False
        
        return True