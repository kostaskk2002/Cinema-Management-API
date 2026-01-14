from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config import get_settings

settings = get_settings()

#Password hashing context me diaforetikes rithmiseis
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  #Perissoteri asfalia
    bcrypt__ident="2b"  #Xrisi tis pio kainourias ekdosis bcrypt
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Elegxei an to plain password tairiazei me to hashed
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Dimiourgei hash apo to password
    """
    #Elegxos megethos password (bcrypt limit einai 72 bytes)
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password is too long (max 72 bytes)")
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Password hashing error: {e}")
        raise


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Dimiourgei JWT token
    
    Args:
        data: Ta dedomena pou tha mpoun sto token (username, user_id, ktl)
        expires_delta: Poso xrono tha einai valid to token
    
    Returns:
        To encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Apokodiopoiei kai elegxei to JWT token
    
    Args:
        token: To JWT token pros elegxo
    
    Returns:
        Ta dedomena tou token an einai valid, alliws None
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_token_for_user(user_id: int, username: str) -> tuple[str, datetime]:
    """
    Dimiourgei token gia sugkekrimeno user
    
    Returns:
        Tuple me (token, expiration_datetime)
    """
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_time = datetime.utcnow() + expires_delta
    
    token_data = {
        "sub": username,
        "user_id": user_id,
        "exp": expire_time
    }
    
    token = create_access_token(token_data)
    
    return token, expire_time