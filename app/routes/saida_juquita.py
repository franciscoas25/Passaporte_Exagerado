from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.database import db
from app.templates_global import templates

router = APIRouter()


@router.get("/saida-juquita", response_class=HTMLResponse)
def form_saida_juquita(request: Request):
    return templates.TemplateResponse(request, "saida_juquita.html", {})


@router.post("/saida-juquita", response_class=HTMLResponse)
def submit_saida_juquita(
    request: Request,
    id_public: str = Form(...),
    qual_renda: str = Form(...),
    quanto_pretende_gastar: str = Form(...),
    com_quem_veio: str = Form(...),
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
        return templates.TemplateResponse(
            request, "resultado.html",
            {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
        )

    resultado = db.registrar_saida_juquita(
        visitante_id=visitante["id"],
        qual_renda=qual_renda,
        quanto_pretende_gastar=quanto_pretende_gastar,
        com_quem_veio=com_quem_veio,
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