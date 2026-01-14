import re
from typing import Tuple


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Elegxei an to username einai valid
    
    Returns:
        Tuple (is_valid, error_message)
    """
    #Toulaxiston 5 xaraktires
    if len(username) < 5:
        return False, "Username prepei na exei toulaxiston 5 xaraktires"
    
    #Prepei na arxizei me gramma
    if not username[0].isalpha():
        return False, "Username prepei na arxizei me gramma"
    
    #Mono alphanumeric kai underscore
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "Username mporei na periexei mono grammata, arithmous kai underscore"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Elegxei an to password einai valid
    
    Returns:
        Tuple (is_valid, error_message)
    """
    #Toulaxiston 8 xaraktires
    if len(password) < 8:
        return False, "Password prepei na exei toulaxiston 8 xaraktires"
    
    #Prepei na exei kefalaia
    if not any(c.isupper() for c in password):
        return False, "Password prepei na periexei toulaxiston ena kefaleo gramma"
    
    #Prepei na exei peza
    if not any(c.islower() for c in password):
        return False, "Password prepei na periexei toulaxiston ena pezo gramma"
    
    #Prepei na exei arithmo
    if not any(c.isdigit() for c in password):
        return False, "Password prepei na periexei toulaxiston enan arithmo"
    
    #Prepei na exei special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password prepei na periexei toulaxiston ena special character"
    
    return True, ""


def validate_token_ownership(token_user_id: int, current_user_id: int) -> bool:
    """
    Elegxei an to token anikei ston swsto user
    
    Returns:
        True an to token anikei ston user, alliws False
    """
    return token_user_id == current_user_id