from fastapi import HTTPException

from ..domain.models import CurrentUser


def require_local_user(user: CurrentUser) -> CurrentUser:
    if not user.id:
        raise HTTPException(status_code=401, detail="缺少当前用户")
    return user
