from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.database import db
from app.templates_global import templates

router = APIRouter()

@router.get("/usuario-pontuacao", response_class=HTMLResponse)
def form_user_pontuacao(request: Request):
    return templates.TemplateResponse(request, "usuario_pontuacao.html", {})

@router.post("/usuario-pontuacao", response_class=HTMLResponse)
def submit_user_pontuacao(request: Request, id_public: str = Form(...)):
    id_public_normalizado = id_public.strip().upper()

    visitante = db.buscar_por_id_public(id_public_normalizado)
    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado_usuario_pontuacao.html",
            {"sucesso": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    dados_usuario = db.buscar_resumo_pontuacao_usuario(id_public=id_public_normalizado)

    return templates.TemplateResponse(
        request, "resultado_usuario_pontuacao.html",
        {"sucesso": True, "usuario": dados_usuario},
    )

    