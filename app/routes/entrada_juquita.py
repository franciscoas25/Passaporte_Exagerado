from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.database import db
from app.templates_global import templates

router = APIRouter()


@router.get("/entrada-juquita", response_class=HTMLResponse)
def form_entrada_juquita(request: Request):
    return templates.TemplateResponse(request, "entrada_juquita.html", {})


@router.post("/entrada-juquita", response_class=HTMLResponse)
def submit_entrada_juquita(
    request: Request,
    id_public: str = Form(...),
    item_ritmo: str = Form(...),
    faixa_etaria: str = Form(...),
    ficou_sabendo_onde: str = Form(...),
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_entrada_juquita(
        visitante_id=visitante["id"],
        item_ritmo=item_ritmo,
        faixa_etaria=faixa_etaria,
        ficou_sabendo_onde=ficou_sabendo_onde,
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