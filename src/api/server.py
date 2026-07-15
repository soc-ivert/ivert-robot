import json
import os
import hashlib
import secrets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from src.core.robot import Robot
from src.api.handlers import MessageHandler

def create_app(robot: Robot) -> FastAPI:

    app = FastAPI()
    app.mount("/static", StaticFiles(directory="src/interface/static"), name="static")
    
    ACCESS_TOKEN = os.getenv("TABLET_ACCESS_TOKEN") # Token de acesso obrigatório
    if not ACCESS_TOKEN:
        raise RuntimeError(
            "TABLET_ACCESS_TOKEN não configurado. Defina essa variável de ambiente antes de iniciar o servidor."
        )

    # HASH do token para armazenar no cookie
    SESSION_VALUE = hashlib.sha256(ACCESS_TOKEN.encode("utf-8")).hexdigest()

    @app.on_event("startup")
    async def startup():
        robot.start()
        print("[SERVER] Robo iniciado")

    @app.get("/")
    async def root(request: Request, token: str = None):

        # Se há token na URL, valida e, se correto, grava cookie e redireciona
        if token is not None:

            if not secrets.compare_digest(token, ACCESS_TOKEN):
                print("[SERVER] Tentativa inválida de acesso com token inválido")
                raise HTTPException(status_code=403, detail="Acesso inválido.")

            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(
                key="tablet_session",
                value=SESSION_VALUE,
                httponly=True,
                samesite="lax",
                max_age=3600 * 24 * 365 * 10,  # 10 anos: sessão de longa duração
            )
            print("[SERVER] Tablet autenticado, cookie de sessão gerado.")
            return response

        # Sem token na URL, exige cookie de sessão válido
        cookie_session = request.cookies.get("tablet_session")
        if cookie_session and secrets.compare_digest(cookie_session, SESSION_VALUE):
            return FileResponse("src/interface/index.html")

        # Nem token nem cookie válido, acesso negado
        print("[SERVER] Tentativa inválida de acesso sem token ou cookie válido")
        raise HTTPException(status_code=403, detail="Acesso inválido.")

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        
        await ws.accept()
        handler = MessageHandler(robot, ws.send_text)

        try:
            while True:
                packet = await ws.receive_text()
                await handler.route(json.loads(packet))

        except WebSocketDisconnect:
            print("[SERVER] Desconectado")

    return app