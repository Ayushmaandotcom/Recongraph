from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging

logger = logging.getLogger("recongraph-api.auth")

SECRET_KEY = "recongraph_enterprise_secret_key_v1" # In prod, load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        tenant_id: str = payload.get("tenant_id")
        if username is None or role is None or tenant_id is None:
            raise credentials_exception
        return {"username": username, "role": role, "tenant_id": tenant_id}
    except JWTError:
        raise credentials_exception

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_auditor(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Auditor access required")
    return current_user

async def require_viewer(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role not in ["admin", "auditor", "viewer"]:
        raise HTTPException(status_code=403, detail="Viewer access required")
    return current_user
