from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.templates_global import templates

from app.database import db

router = APIRouter()


@router.get("/cenografia", response_class=HTMLResponse)
def form_cenografia(request: Request):
    return templates.TemplateResponse(request, "cenografia.html", {})


@router.post("/cenografia", response_class=HTMLResponse)
def submit_cenografia(
    request: Request,
    id_public: str = Form(...),
    oque_mais_garimpou: str = Form(...),
    qual_marca_deixou_louco: str = Form(...)
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_cenografia(
        visitante_id=visitante["id"],
        oque_mais_garimpou=oque_mais_garimpou,
        qual_marca_deixou_louco=qual_marca_deixou_louco
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