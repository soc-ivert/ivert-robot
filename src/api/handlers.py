# src/api/handlers.py
import asyncio
import json
import cv2
import base64
import numpy as np

from src.core.robot import Robot
from src.core.enums import RobotState

IDLE_TIMEOUT = 30

class MessageHandler:
    """ Coordena o fluxo de interação do robô.

    Recebe eventos do tablet via WebSocket, gerencia transições de estado
    e aciona as capacidades do Robot conforme necessário. Também reage
    a eventos internos do Robot, como detecção de rosto.
    """

    def __init__(self, robot: Robot, send):
        """ Inicializa o handler e registra o callback de detecção facial.

        Args:
            robot: Instância do Robot contendo os componentes do sistema.
            send: Função assíncrona para envio pelo WebSocket.
        """
        self._robot = robot
        self._send = send
        self._robot.set_face_callback(self.on_face_detected)
        self._sleep_task: asyncio.Task | None = None


    async def route(self, message: dict):
        """ Roteia uma mensagem recebida pelo WebSocket ao handler correspondente.

        Args:
            message: Dicionário com as chaves 'type' e 'data'.
        """
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


    async def handle_frame(self, data: dict):
        """ Decodifica e encaminha um frame de vídeo ao Robot.

        Args:
            data: Dicionário contendo a imagem codificada em Base64 sob a chave 'image'.
        """

        frame_bytes = base64.b64decode(data["image"])
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    
        if frame is not None:
            self._robot.push_frame(frame)


    async def handle_ask(self, data: dict):
        """ Processa uma pergunta do visitante e envia a resposta ao tablet.

        Ignorada se o robô não estiver em um estado receptivo.
        Transiciona para THINKING durante o processamento e SPEAKING ao responder.

        Args:
            data: Dicionário contendo o texto da pergunta sob a chave 'text'.
        """
        robot_state = self._robot.get_current_state()
        ask:str = data["text"]
        activation_words = ["oi robo", "oi robô", "ei robo", "ei robô"]

        if robot_state not in [RobotState.WAITING, RobotState.SLEEPING, RobotState.GREETING]:
            return

        if robot_state in [RobotState.SLEEPING, RobotState.GREETING]:
            if not any(word in ask.lower() for word in activation_words):
                return

        print("[SERVER] Pergunta recebida:", ask)
        await self.change_state(RobotState.THINKING)

        answer = await asyncio.to_thread(self._robot.send_ask, ask)
        await self._send(json.dumps({
            "type": "answer",
            "data": { "text": answer if answer is not None else "error"}
        }))

        print("[SERVER] Resposta enviada:", answer)
        await self.change_state(RobotState.SPEAKING)


    async def handle_speech_end(self, data: dict):
        """ Notificado pelo tablet ao concluir a fala de uma resposta.

        Retorna o robô ao estado WAITING, reiniciando o timer de inatividade.

        Args:
            data: Payload do evento (não utilizado).
        """
        print("[SPEECH_END] Fim de fala recebido")
        await self.change_state(RobotState.WAITING)


    async def change_state(self, state: RobotState):
        """ Altera o estado do robô e notifica o tablet.

        Gerencia o timer de inatividade conforme o novo estado: reinicia em GREETING e WAITING, 
        cancela em SLEEPING. Ao dormir, reinicia a interação limpando histórico e encoding.

        Args:
            state: Novo estado a ser aplicado.
        """

        print(f"[HANDLER] Estado alterado de _{self._robot.get_current_state()}_ para _{state.value}_", )
        self._robot.set_state(state)

        # Envia o novo estado através do WebSocket
        await self._send(json.dumps({
            "type": "state",
            "data": { 
                "value": state.value 
            }
        }))

        if state in [RobotState.GREETING, RobotState.WAITING]:
            self._reset_sleep_timer()
        elif state == RobotState.SLEEPING:
            self._cancel_sleep_timer()
            self._robot.reset_interaction()
        elif state in [RobotState.SPEAKING, RobotState.THINKING]:
            self._cancel_sleep_timer()


    async def on_face_detected(self):
        """ Callback acionado pelo Robot ao detectar um rosto.

        Transiciona para GREETING apenas se o robô estiver em SLEEPING,
        evitando reinicializações durante interações ativas.
        """
        if self._robot.get_current_state() == RobotState.SLEEPING:
            await self.change_state(RobotState.GREETING)


    def _reset_sleep_timer(self) -> None:
        """ Cancela o timer atual e inicia um novo.
        """
        self._cancel_sleep_timer()
        self._sleep_task = asyncio.create_task(self._sleep_timeout())


    def _cancel_sleep_timer(self) -> None:
        """ Cancela o timer de inatividade se estiver ativo.
        """
        if self._sleep_task and not self._sleep_task.done():
            self._sleep_task.cancel()
            self._sleep_task = None


    async def _sleep_timeout(self) -> None:
        """ Aguarda o tempo de inatividade e transiciona para SLEEPING.
        
        Cancelada automaticamente ao resetar o timer.
        """
        await asyncio.sleep(IDLE_TIMEOUT)
        await self.change_state(RobotState.SLEEPING)