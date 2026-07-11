from fastapi import Header, Request

from ..domain.models import CurrentUser


def get_current_user(request: Request, x_user: str = Header(default="")) -> CurrentUser:
    default_user = request.app.state.settings.get("web.default_user", "local-user")
    user_id = x_user.strip() or default_user
    return CurrentUser(id=user_id, display_name=user_id)
