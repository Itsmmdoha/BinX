from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Callable
from auth import Token
from models.shared import Role

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    try:
        payload = Token.get_payload(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")


def require_role(required_role: Role) -> Callable:
    def enforce_role(token_payload: dict = Depends(get_token_payload)):
        role = token_payload.get("role")
        if role != required_role:
            raise HTTPException(status_code=403, detail="Forbidden Operation")
    return enforce_role
