import os
from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse
from app.templates_global import templates

from app.database import db
from app.services.public_code import gerar_public_code_unico
from app.dependencies import verificar_admin
router = APIRouter()

BASE_URL = os.environ["base_url"]

@router.get("/admin/lojas/nova", dependencies=[Depends(verificar_admin)])
def form_nova_loja(request: Request):
    return templates.TemplateResponse(request, "admin_nova_loja.html", {})


@router.post("/admin/lojas/nova", response_class=HTMLResponse, dependencies=[Depends(verificar_admin)])
def submit_nova_loja(
    request: Request,
    nome: str = Form(...),
    pontos_base: int = Form(...),
):
    codigo = gerar_public_code_unico(db.codigo_loja_existe)
    loja = db.inserir_loja(codigo_publico=codigo, nome=nome, pontos_base=pontos_base)

    if loja is None:
        return templates.TemplateResponse(
            request, "admin_resultado_loja.html",
            {"sucesso": False, "mensagem": "Erro ao cadastrar a loja. Tenta de novo."},
            status_code=500,
        )

    url_loja = f"{BASE_URL}/loja/{loja['codigo_publico']}"

    return templates.TemplateResponse(
        request, "admin_resultado_loja.html",
        {"sucesso": True, "loja": loja, "url_loja": url_loja},
    )

@router.get("/admin/brindes/nova", response_class=HTMLResponse, dependencies=[Depends(verificar_admin)])
def form_novo_brinde(request: Request):
    return templates.TemplateResponse(request, "admin_novo_brinde.html", {})


@router.post("/admin/brindes/nova", response_class=HTMLResponse, dependencies=[Depends(verificar_admin)])
def submit_novo_brinde(
    request: Request,
    nome: str = Form(...),
    custo_pontos: int = Form(...),
    estoque: int = Form(...),
    tipo: str = Form(...),
):
    brinde = db.inserir_brinde(nome=nome, custo_pontos=custo_pontos, estoque=estoque, tipo=tipo)

    if brinde is None:
        return templates.TemplateResponse(
            request, "admin_resultado_brinde.html",
            {"sucesso": False, "mensagem": "Erro ao cadastrar o brinde. Tenta de novo."},
            status_code=500,
        )

    return templates.TemplateResponse(
        request, "admin_resultado_brinde.html",
        {"sucesso": True, "brinde": brinde},
    )


@router.get("/admin/resgate/brindes")
def buscar_brindes_resgate(id_public: str = Query(...)):

    id_public = id_public.strip().upper()

    cliente = db.buscar_por_id_public(id_public)

    if not cliente:
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente não encontrado."}
        )

    brindes = db.buscar_brindes_disponiveis_por_visitante(pontos=cliente["pontos_atuais"], visitante_id=cliente["id"])

    return brindes


@router.get("/admin/resgate", response_class=HTMLResponse, dependencies=[Depends(verificar_admin)])
def form_resgate(request: Request):
    brindes = db.buscar_brindes_disponiveis()
    return templates.TemplateResponse(request, "admin_resgate.html", {"brindes": brindes})


@router.post("/admin/resgate", response_class=HTMLResponse, dependencies=[Depends(verificar_admin)])
def submit_resgate(request: Request, id_public: str = Form(...), brinde_id: int = Form(...)):
    visitante = db.buscar_por_id_public(id_public.strip().upper())
    if visitante is None:
        return templates.TemplateResponse(
            request, "admin_resultado_resgate.html",
            {"sucesso": False, "mensagem": "Código não encontrado."},
        )

    brinde = db.buscar_brinde(brinde_id)
    if brinde is None:
        return templates.TemplateResponse(
            request, "admin_resultado_resgate.html",
            {"sucesso": False, "mensagem": "Brinde não encontrado."},
        )

    resultado = db.resgatar_brinde(
    visitante_id=visitante["id"],
    brinde_id=brinde_id,
    custo_pontos=brinde["custo_pontos"],
    tipo=brinde["tipo"],
)

    mensagens = {
        "ok": f"✅ {visitante['nome']} resgatou: {brinde['nome']}!",
        "saldo_insuficiente": f"{visitante['nome']} não tem pontos suficientes.",
        "sem_estoque": f"{brinde['nome']} está sem estoque.",
        "formularios_incompletos": f"{visitante['nome']} ainda não respondeu todos os formulários.",
        "cadastro_fora_periodo": f"{visitante['nome']} não se cadastrou no período de 19 a 22/09.",
        "ja_resgatou_padrao": f"{visitante['nome']} já resgatou o brinde dele.",
        "duplicado": f"{visitante['nome']} já resgatou esse item antes.",
        "erro": "Erro ao processar o resgate. Tenta de novo.",
        "formularios_incompletos_fora_periodo": f"{visitante['nome']} ainda não respondeu todos os formulários e não se cadastrou dentro do período 19/09 a 22/09.",
    }

    return templates.TemplateResponse(
        request, "admin_resultado_resgate.html",
        {"sucesso": resultado == "ok", "mensagem": mensagens[resultado]},
    )

@router.get("/admin/dashboard", dependencies=[Depends(verificar_admin)])
def form_dashboard(request: Request):
    total_visitantes = db.buscar_total_visitantes()
    total_lojas = db.buscar_total_lojas()
    total_brindes = db.buscar_total_brindes()
    return templates.TemplateResponse(request, "dashboard.html", {"total_visitantes": total_visitantes, "total_lojas": total_lojas, "total_brindes": total_brindes})

@router.post("/admin/brinde/listar", response_class=HTMLResponse)
def listar_brindes(request: Request):
    brindes = db.listar_brindes()
    if brindes is None:
        return templates.TemplateResponse(
            request, "dashboard.html",
            {"mensagem": "Loja não encontrado."},
            status_code=404,
        )
    return templates.TemplateResponse(request, "dashboard.html", {"brindes": brindes})

@router.get("/admin/usuario_pontuacao", dependencies=[Depends(verificar_admin)])
def form_usuario_pontuacao(request: Request):
    return templates.TemplateResponse(request, "usuario_pontuacao.html", {})