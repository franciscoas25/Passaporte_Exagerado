from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.templates_global import templates
from typing import Optional

from app.database import db

router = APIRouter()


@router.get("/saida-nps", response_class=HTMLResponse)
def form_saida_nps(request: Request):
    return templates.TemplateResponse(request, "saida_nps.html", {})


@router.post("/saida-nps", response_class=HTMLResponse)
def submit_saida_nps(
    request: Request,
    id_public: str = Form(...),
    quanto_recomenda: int = Form(..., ge=0, le=10),
    maior_destaque: str = Form(...),
    te_vejo_proxima_edicao: str = Form(...),
    feedback: Optional[str] = Form(None)
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_saida_nps(
        visitante_id=visitante["id"],
        quanto_recomenda=quanto_recomenda,
        maior_destaque=maior_destaque,
        te_vejo_proxima_edicao=te_vejo_proxima_edicao,
        feedback=feedback
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