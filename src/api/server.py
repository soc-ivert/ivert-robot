import base64
import numpy as np
import cv2

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.core.robot import Robot

def create_app(robot: Robot) -> FastAPI:

    app = FastAPI()
    app.mount("/static", StaticFiles(directory="src/interface/static"), name="static")

    @app.get("/")
    async def root():
        return FileResponse("src/interface/index.html")

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        
        # Aceita a conexão
        await ws.accept()

        try:
            while True:
                frame_base64 = await ws.receive_text() # Recebe os frames como string Base64
                frame_bytes = base64.b64decode(frame_base64) # Converte a string para bytes
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8) # Converte em um array numpy uint8
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR) # Decodifica o array

                # Se falhar ignora e continua
                if frame is None:
                    continue

                robot.push_frame(frame)

        except WebSocketDisconnect:
            print("Desconectado")

    return app