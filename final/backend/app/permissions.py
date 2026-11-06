"""Permission and role utilities for the CropSentinel backend.
The design follows a simple enum‑based role model and FastAPI dependencies.
"""

from enum import Enum
from typing import List

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Simple role enumeration – extend as needed
class Role(str, Enum):
    farmer = "farmer"
    extension_worker = "extension_worker"
    admin = "admin"

# Dummy token verification – replace with real JWT/OTP logic later
_security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> dict:
    """Extract a user dict from the Authorization header.
    For now we only decode a fake ``role`` passed as ``Bearer <role>``.
    A proper implementation would verify JWT signatures, expiry, etc.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    # Expect token to be exactly the role name for this stub implementation
    if token not in {role.value for role in Role}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role token")
    return {"role": token}

def require_roles(required: List[Role]):
    """Dependency that ensures the current user has one of the required roles.
    Usage::
        @app.get("/admin")
        def admin_endpoint(user=Depends(require_roles([Role.admin]))):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)):
        if user["role"] not in [r.value for r in required]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency

