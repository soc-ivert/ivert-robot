import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.core.robot import Robot
from src.api.handlers import MessageHandler

def create_app(robot: Robot) -> FastAPI:

    app = FastAPI()
    app.mount("/static", StaticFiles(directory="src/interface/static"), name="static")

    @app.on_event("startup")
    async def startup():
        robot.start()
        print("[SERVER] Robo iniciado")

    @app.get("/")
    async def root():
        return FileResponse("src/interface/index.html")

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