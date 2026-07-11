from fastapi import Request

from ..service.knowledge_service import KnowledgeService


def get_knowledge_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge_service
