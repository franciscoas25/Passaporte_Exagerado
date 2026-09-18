import os
import secrets
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_global import templates
from dotenv import load_dotenv
from app.dependencies import verificar_admin

router = APIRouter()

load_dotenv()

ADMIN_USER = os.getenv("admin_user")
ADMIN_PASSWORD = os.getenv("admin_password")

@router.get("/admin/login", response_class=HTMLResponse)
def form_login(request: Request):
    return templates.TemplateResponse(request, "admin_login.html", {})


@router.post("/admin/login", response_class=HTMLResponse)
def submit_login(request: Request, usuario: str = Form(...), senha: str = Form(...)):
    usuario_ok = secrets.compare_digest(usuario, ADMIN_USER)
    senha_ok = secrets.compare_digest(senha, ADMIN_PASSWORD)

    if usuario_ok and senha_ok:
        request.session["autenticado"] = True
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request, "admin_login.html",
        {"erro": "Usuário ou senha incorretos."},
    )


@router.get("/admin", response_class=HTMLResponse, dependencies=[Depends(verificar_admin)])
def hub_admin(request: Request):
    return templates.TemplateResponse(request, "admin_hub.html", {})


@router.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)