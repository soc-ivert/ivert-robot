import base64
import numpy as np
import cv2
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.core.robot import Robot

def decode_frame(frame_base64):

    frame_bytes = base64.b64decode(frame_base64) # Converte a string para bytes
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8) # Converte em um array numpy uint8
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR) # Decodifica o array

    return frame

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

                packet = await ws.receive_text() # Recebe JSON
                message = json.loads(packet)
                type = message.get("type")
                data = message.get("data", {})

                if type == "frame":
                    frame = decode_frame(data["image"])
                    
                    if frame is None: # Se falhar ignora e continua
                        continue
                    
                    robot.push_frame(frame)

                elif type == "ask":

                    print("[SERVER] Pergunta recebida:", data["text"])

                    answer = robot.send_ask(data["text"])
                    await ws.send_text(json.dumps({
                        "type": "answer",
                        "data": {"text": answer}
                    }))

                    print("[SERVER] Resposta enviada:", answer)

                elif type == "user_data":
                    pass

        except WebSocketDisconnect:
            print("Desconectado")

    return app