from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.templates_global import templates

from app.database import db

router = APIRouter()


@router.get("/dentro-lojas", response_class=HTMLResponse)
def form_dentro_lojas(request: Request):
    return templates.TemplateResponse(request, "dentro_lojas.html", {})


@router.post("/dentro-lojas", response_class=HTMLResponse)
def submit_dentro_lojas(
    request: Request,
    id_public: str = Form(...),
    melhor_dia: str = Form(...),
    forma_pagamento: str = Form(...)
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_dentro_lojas(
        visitante_id=visitante["id"],
        melhor_dia=melhor_dia,
        forma_pagamento=forma_pagamento
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