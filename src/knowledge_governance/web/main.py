from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config.config import load_settings, validate_settings
from .controller.catalog_api import router as catalog_router
from .controller.evidence_api import router as evidence_router
from .controller.health_api import router as health_router
from .controller.knowledge_api import router as knowledge_router
from .controller.lifecycle_api import knowledge_transition_router, router as lifecycle_router
from .controller.meta_api import router as meta_router
from .controller.pages import configure_templates, router as pages_router
from .exceptions.exception_handler import register_exception_handlers
from .middlewares.request_logging import register_request_logging
from .service.knowledge_service import KnowledgeService

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = Path(__file__).parent


def create_app(root: Path, environment: str = "development") -> FastAPI:
    root = root.resolve()
    settings = load_settings(environment)
    validate_settings(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        required = ("schemas", "policies", "templates")
        missing = [name for name in required if not (root / name).exists()]
        if missing:
            raise RuntimeError("知识库缺少目录：" + "、".join(missing))
        LOGGER.info("knowledge web started root=%s environment=%s", root, environment)
        yield
        LOGGER.info("knowledge web stopped")

    app = FastAPI(
        title="Knowledge Base 管理界面",
        version="0.1.0",
        description="以 Markdown、Evidence 和 Git 为事实来源的本地知识管理 API",
        lifespan=lifespan,
    )
    app.state.root = root
    app.state.settings = settings
    app.state.knowledge_service = KnowledgeService(root)

    templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
    configure_templates(templates)
    app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")

    register_request_logging(app)
    register_exception_handlers(app)
    for router in (health_router, meta_router, knowledge_router, evidence_router, lifecycle_router, knowledge_transition_router, catalog_router, pages_router):
        app.include_router(router)
    return app
