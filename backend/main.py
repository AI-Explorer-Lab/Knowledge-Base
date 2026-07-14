from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.config import settings as default_settings
from backend.controller import (
    business_domain_api,
    health_api,
    identity_api,
    knowledge_api,
    member_api,
)
from backend.database.lifecycle import close_database, init_database
from backend.exceptions.exception_handler import install_exception_handlers
from backend.middlewares.auth_dependency import IdentityService
from backend.middlewares.request_logging import RequestLoggingMiddleware
from backend.service.knowledge_service import KnowledgeService
from backend.service.knowledge_template_service import KnowledgeTemplateService
from backend.service.business_domain_service import BusinessDomainService
from backend.service.member_service import MemberService
from backend.service.preview_token_service import PreviewTokenService
from backend.service.repository_lock import RepositoryWriteLock


def create_app(settings: Any = None) -> FastAPI:
    settings = settings or default_settings
    logging.basicConfig(
        level=getattr(logging, str(settings.log_level).upper(), logging.INFO),
        format="%(message)s",
    )

    write_lock = RepositoryWriteLock(settings.repo_root)
    member_service = MemberService(settings.repo_root, write_lock)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Fail startup before serving traffic when the repository identity
        # boundary is malformed or the fixed local actor is not active.
        member_service.load_config()
        if settings.environment_name in {"development", "test"}:
            member_service.get_member(settings.dev_actor)
        try:
            await init_database(settings)
            yield
        finally:
            await close_database()

    app = FastAPI(
        title="Knowledge Base API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.environment_name != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.environment_name != "production" else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=[
            "Content-Type",
            "X-Request-ID",
            "X-Knowledge-Actor",
            "X-Knowledge-Timestamp",
            "X-Knowledge-Signature",
        ],
    )
    app.add_middleware(RequestLoggingMiddleware)

    token_service = PreviewTokenService(settings.preview_secret, settings.preview_ttl_seconds)
    app.state.settings = settings
    app.state.identity = IdentityService(settings)
    app.state.members = member_service
    app.state.business_domains = BusinessDomainService(member_service, write_lock)
    app.state.knowledge_templates = KnowledgeTemplateService(member_service)
    app.state.knowledge = KnowledgeService(
        settings.repo_root,
        member_service,
        write_lock,
        token_service,
    )

    install_exception_handlers(app)
    app.include_router(health_api.router)
    app.include_router(identity_api.router)
    app.include_router(knowledge_api.router)
    app.include_router(member_api.router)
    app.include_router(business_domain_api.router)
    return app


app = create_app()
