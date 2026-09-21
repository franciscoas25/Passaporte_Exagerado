from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.database import db
from app.templates_global import templates

router = APIRouter()

@router.get("/tudao", response_class=HTMLResponse)
def form_acao_guerrilha(request: Request):
    return templates.TemplateResponse(request, "tudao.html", {})

@router.post("/tudao", response_class=HTMLResponse)
def submit_tudao(
    request: Request,
    id_public: str = Form(...),
    quem_e_voce: str = Form(...),
    foco_principal: str = Form(...),
    regiao_origem: str = Form(...),
    como_veio_exagerado: str = Form(...),
    tempo_ate_chegar: str = Form(...),
    ritmo_do_item: str = Form(...),
    faixa_idade: str = Form(...),
    como_ficou_sabendo: str = Form(...),
    maior_garimpo: str = Form(...),
    marca_favorita: str = Form(...),
    prioridade_lounge_vip: str = Form(...),
    quantidade_sacolas: str = Form(...),
    faixa_renda: str = Form(...),
    valor_gasto: str = Form(...),
    companhia_role: str = Form(...),
    melhor_dia: str = Form(...),
    forma_pagamento: str = Form(...),
    nota_recomendacao: int = Form(...),
    maior_destaque: str = Form(...),
    proxima_edicao_sp: str = Form(...),
    feedback_geral: str = Form(...),
):
    visitante = db.buscar_por_id_public(id_public.strip().upper())

    if visitante is None:
            return templates.TemplateResponse(
                request, "resultado.html",
                {"sucesso": False, "ja_respondeu": False, "mensagem": "Código não encontrado. Confere se digitou certo."},
            )

    resultado = db.registrar_tudao(
            visitante_id=visitante["id"],
            quem_e_voce=quem_e_voce,
            foco_principal=foco_principal,
            regiao_origem=regiao_origem,
            como_veio_exagerado=como_veio_exagerado,
            tempo_ate_chegar=tempo_ate_chegar,
            ritmo_do_item=ritmo_do_item,
            faixa_idade=faixa_idade,
            como_ficou_sabendo=como_ficou_sabendo,
            maior_garimpo=maior_garimpo,
            marca_favorita=marca_favorita,
            prioridade_lounge_vip=prioridade_lounge_vip,
            quantidade_sacolas=quantidade_sacolas,
            faixa_renda=faixa_renda,
            valor_gasto=valor_gasto,
            companhia_role=companhia_role,
            melhor_dia=melhor_dia,
            forma_pagamento=forma_pagamento,
            nota_recomendacao=nota_recomendacao,
            maior_destaque=maior_destaque,
            proxima_edicao_sp=proxima_edicao_sp,
            feedback_geral=feedback_geral,
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