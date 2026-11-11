"""Security, JWT authentication, and Role-gating.
Adheres to h_uc.puml actor-to-usecase role restrictions and Req 1.1, 1.2, 16.1.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Callable
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from asghi.domain.enums import UserRole
from asghi.domain.user import User

SECRET_KEY = "asghi-fusha-listening-secret-key-prod-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: UUID, roles: List[UserRole]) -> str:
    """Generate JWT token with user identity and roles."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "roles": [r.value for r in roles],
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """FastAPI dependency to extract current authenticated user."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload["sub"]
    from asghi.repository import get_repository
    try:
        user_uuid = UUID(user_id_str)
        user = get_repository().get_user_by_id(user_uuid)
        if user:
            return user
    except ValueError:
        pass

    for u in User._registry:
        if str(u.userId) == user_id_str:
            try:
                get_repository().save_user(u)
            except Exception:
                pass
            return u

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
    )


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """FastAPI dependency factory to gate endpoints strictly to actor roles per h_uc.puml."""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        user_role_values = {prof.role for prof in user.userProfiles}
        # Admin can access administrative functions; check if any allowed role matches
        allowed_set = set(allowed_roles)
        if not user_role_values.intersection(allowed_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles {[r.value for r in allowed_roles]}",
            )
        return user

    return role_checker
