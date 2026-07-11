from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request):
    return {"status": "ok", "environment": request.app.state.settings.get("environment", "unknown")}
