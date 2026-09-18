from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.templates_global import templates

from app.database import db

router = APIRouter()


@router.get("/estacionamento", response_class=HTMLResponse)
def form_estacionamento(request: Request):
    return templates.TemplateResponse(request, "estacionamento.html", {})


@router.post("/estacionamento", response_class=HTMLResponse)
def submit_estacionamento(
    request: Request,
    id_public: str = Form(...),
    como_veio: str = Form(...),
    quanto_tempo: str = Form(...),
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_estacionamento(
        visitante_id=visitante["id"],
        como_veio=como_veio,
        quanto_tempo=quanto_tempo,
    )

    if resultado == "ok":
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": True, "ja_respondeu": False, "mensagem": f"Valeu, {visitante['nome']}! Sua resposta foi registrada."},
        )
    elif resultado == "duplicado":
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": True, "mensagem": "Você já passou por aqui hoje!"},
        )
    else:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Não conseguimos registrar agora. Tenta de novo."},
            status_code=500,
        )