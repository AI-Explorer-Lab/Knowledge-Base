from .catalog_api import router as catalog_router
from .evidence_api import router as evidence_router
from .health_api import router as health_router
from .knowledge_api import router as knowledge_router
from .lifecycle_api import router as lifecycle_router
from .pages import router as pages_router

__all__ = ["catalog_router", "evidence_router", "health_router", "knowledge_router", "lifecycle_router", "pages_router"]
