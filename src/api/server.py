import json
import os
import time
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
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_SECONDS = 600  # 10 minutos bloqueado após exceder o limite
    _failed_attempts: dict[str, list[float]] = {}

    def _is_locked_out(client_ip: str) -> bool:

        now = time.time()
        recent = [t for t in _failed_attempts.get(client_ip, []) if now - t < LOCKOUT_SECONDS]
        _failed_attempts[client_ip] = recent

        return len(recent) >= MAX_FAILED_ATTEMPTS

    def _register_failure(client_ip: str) -> None:
        _failed_attempts.setdefault(client_ip, []).append(time.time())

    @app.on_event("startup")
    async def startup():
        robot.start()
        print("[SERVER] Robo iniciado")

    @app.get("/")
    async def root(request: Request, token: str = None):

        client_ip = request.client.host if request.client else "unknown"

        # Se há token na URL, valida e, se correto, grava cookie e redireciona
        if token is not None:

            if _is_locked_out(client_ip):
                print(f"[SERVER] IP {client_ip} bloqueado por excesso de tentativas com token inválido")
                raise HTTPException(
                    status_code=429,
                    detail="Muitas tentativas inválidas. Tente novamente mais tarde."
                )

            if not secrets.compare_digest(token, ACCESS_TOKEN):
                _register_failure(client_ip)
                print(f"[SERVER] Tentativa inválida de acesso com token inválido (IP {client_ip})")
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

        # Valida Origin x Host (proteção CSWSH)
        origin = ws.headers.get("origin") # de onde a página que iniciou a conexão foi carregada.
        host = ws.headers.get("host") # endereço que o cliente usou para chegar até este servidor

        allowed_origins = set()
        if host:
            allowed_origins.add(f"http://{host}")
            allowed_origins.add(f"https://{host}")

        if origin and origin not in allowed_origins:
            print(f"[SERVER] Conexão WebSocket rejeitada: origem não autorizada ({origin})")
            await ws.close(code=1008)
            return

        # Validação do cookie de sessão (Passo 3)
        cookie_session = ws.cookies.get("tablet_session")
        if not cookie_session or not secrets.compare_digest(cookie_session, SESSION_VALUE):
            print("[SERVER] Conexão WebSocket rejeitada: cookie de sessão ausente ou inválido")
            await ws.close(code=1008)
            return

        await ws.accept()
        handler = MessageHandler(robot, ws.send_text)

        try:
            while True:
                packet = await ws.receive_text()
                await handler.route(json.loads(packet))

        except WebSocketDisconnect:
            print("[SERVER] Desconectado")

    return app