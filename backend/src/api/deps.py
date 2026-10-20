from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.db.models import User
from src.db.session import get_db
from src.utils.auth import bearer_scheme, decode_token

# Dev identity: every request runs as user 1 until real auth is wired. This is a
# seam — swap the body of get_current_user_id() to `return get_current_user(...).id`
# and no route signature below changes (see ARCHITECTURE §1 "swap bodies, not contracts").
DEV_USER_ID = 1


def get_current_user_id() -> int:
    return DEV_USER_ID


CurrentUserId = Annotated[int, Depends(get_current_user_id)]


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),  
    db: Session = Depends(get_db),                                       
) -> User:
    payload = decode_token(credentials.credentials)                      
    if payload.get("type") != "access":                                  
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    user_id = payload.get("sub")
    if user_id is None:                                                  
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")
    user = db.get(User, int(user_id))                                   
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user                                                          
