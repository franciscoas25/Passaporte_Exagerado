from fastapi import FastAPI
from app.routes import entrada_juquita, visitante, loja, vip_lounge, admin, usuario_pontuacao, auth, acao_guerrilha, boas_vindas, estacionamento, cenografia, saida_juquita, dentro_lojas, saida_nps
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
load_dotenv()

app = FastAPI(title="Ecossistema de Dados Exagerado")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("session_create_key"), max_age=3600)

@app.get("/")
def redirect_to_entrada():
    return RedirectResponse(url="/entrada")

app.include_router(visitante.router)
app.include_router(loja.router)
app.include_router(entrada_juquita.router)
app.include_router(vip_lounge.router)
app.include_router(admin.router)
app.include_router(usuario_pontuacao.router)
app.include_router(auth.router)
app.include_router(acao_guerrilha.router)
app.include_router(boas_vindas.router)
app.include_router(estacionamento.router)
app.include_router(cenografia.router)
app.include_router(saida_juquita.router)
app.include_router(dentro_lojas.router)
app.include_router(saida_nps.router)