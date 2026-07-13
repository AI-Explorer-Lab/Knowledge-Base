from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Request, Response, status

from backend.database.lifecycle import database_is_ready
from backend.domain.res import HealthResponse


router = APIRouter(tags=["health"])


async def _health_payload(request: Request, response: Response) -> Dict[str, str]:
    repo: Path = request.app.state.settings.repo_root
    repository_ready = (repo / "knowledge-catalog.md").is_file() and (
        repo / ".knowledge-config.yaml"
    ).is_file()
    database_ready = await database_is_ready()
    healthy = repository_ready and database_ready
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if healthy else "degraded",
        "service": "knowledge-base-backend",
        "database": "ready" if database_ready else "unavailable",
        "repository": "ready" if repository_ready else "unavailable",
    }


@router.get("/health", response_model=HealthResponse)
async def health(request: Request, response: Response) -> Dict[str, str]:
    return await _health_payload(request, response)


@router.get("/api/health", response_model=HealthResponse)
async def api_health(request: Request, response: Response) -> Dict[str, str]:
    return await _health_payload(request, response)
