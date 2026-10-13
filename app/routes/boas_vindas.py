from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.database import db
from app.templates_global import templates

router = APIRouter()


@router.get("/boas-vindas", response_class=HTMLResponse)
def form_boas_vindas(request: Request):
    return templates.TemplateResponse(request, "boas_vindas.html", {})


@router.post("/boas-vindas", response_class=HTMLResponse)
def submit_boas_vindas(
    request: Request,
    id_public: str = Form(...),
    quem_eh_voce: str = Form(...),
    qual_foco: str = Form(...),
    regiao: str = Form(...),
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_boas_vindas(
        visitante_id=visitante["id"],
        quem_eh_voce=quem_eh_voce,
        qual_foco=qual_foco,
        regiao=regiao,
    )

    if resultado == "ok":
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": True, "ja_respondeu": False, "mensagem": f"Valeu, {visitante['nome']}! Sua mensagem foi registrada."},
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