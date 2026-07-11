from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)
templates: Jinja2Templates


def configure_templates(value: Jinja2Templates) -> None:
    global templates
    templates = value


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"repository": request.app.state.root.name})
