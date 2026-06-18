# src/api/handlers.py
import json
import cv2
import base64
import numpy as np

from src.core.robot import Robot
from src.core.enums import RobotState

class MessageHandler:

    def __init__(self, robot: Robot, send):
        self._robot = robot
        self._send = send # função que envia texto pelo ws
        self._robot.set_face_callback(self.on_face_detected)

    async def on_face_detected(self):
        if self._robot.get_current_state() == RobotState.SLEEPING:
            await self.change_state(RobotState.GREETING)

    async def change_state(self, state: RobotState):

        if state == RobotState.SLEEPING:
            self._robot.reset_interaction()

        print(f"[HANDLER] Estado alterado de _{self._robot.get_current_state()}_ para _{state.value}_", )
        self._robot.set_state(state)

        # Envia o novo estado através do WebSocket
        await self._send(json.dumps({
            "type": "state",
            "data": { 
                "value": state.value 
            }
        }))

    async def handle_frame(self, data: dict):

        frame_bytes = base64.b64decode(data["image"])
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    
        if frame is not None:
            self._robot.push_frame(frame)

    async def handle_ask(self, data: dict):

        if self._robot.get_current_state() not in [RobotState.WAITING, RobotState.SLEEPING, RobotState.GREETING]:
            return

        print("[SERVER] Pergunta recebida:", data["text"])
        await self.change_state(RobotState.THINKING)

        answer = self._robot.send_ask(data["text"])
        await self._send(json.dumps({
            "type": "answer",
            "data": { "text": answer }
        }))

        print("[SERVER] Resposta enviada:", answer)
        await self.change_state(RobotState.SPEAKING)

    async def handle_speech_end(self, data: dict):
        await self.change_state(RobotState.WAITING)

    async def route(self, message: dict):

        type = message.get("type")
        data = message.get("data", {})

        routes = {
            "frame": self.handle_frame,
            "ask": self.handle_ask,
            "speech_end": self.handle_speech_end,
        }

        handler = routes.get(type)
        if handler:
            await handler(data)
        else:
            print("[SERVER] Tipo desconhecido:", type)