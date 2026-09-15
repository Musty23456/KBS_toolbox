from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.token import RevokedToken
from app.models.user import RoleName, User
from app.security import TokenError, safe_decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = safe_decode_token(token)
    except TokenError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    jti = payload.get("jti")
    if jti and db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: Iterable[RoleName]):
    """Dependency factory: require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)"""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency
