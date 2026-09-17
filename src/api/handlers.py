# src/api/handlers.py
import asyncio
import json
import cv2
import base64
import numpy as np

from src.core.robot import Robot
from src.core.enums import RobotState

IDLE_TIMEOUT = 30
BUSY_TIMEOUT = 60

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
        self._disposed = False

    async def _safe_send(self, payload: dict) -> bool:
        """ Envia dados pelo WebSocket tr caso a conexão esteja fechada.
        """
        if self._disposed:
            return False
        try:
            await self._send(json.dumps(payload))
            return True
        except Exception as e:
            print(f"[HANDLER] Falha ao enviar via WebSocket ({payload.get('type')}): {e}")
            return False

    async def send_initial_state(self):
        """ Envia o estado atual do robô ao tablet conectado para sincronizar ao conectar/reconectar.
        """
        state = self._robot.get_current_state()
        print(f"[HANDLER] Enviando estado inicial: {state.value}")
        
        await self._safe_send({
            "type": "state",
            "data": { 
                "value": state.value 
            }
        })

        # Sincroniza o timer para o estado atual se não estiver em SLEEPING
        if state in [RobotState.GREETING, RobotState.WAITING]:
            self._reset_sleep_timer(IDLE_TIMEOUT)
        elif state in [RobotState.THINKING, RobotState.SPEAKING]:
            self._reset_sleep_timer(BUSY_TIMEOUT)

    def dispose(self):
        """ Libera recursos do handler ao desconectar ou ser substituído por um novo.
        """
        self._disposed = True
        self._cancel_sleep_timer()

    async def route(self, message: dict):
        """ Roteia uma mensagem recebida pelo WebSocket ao handler correspondente.

        Args:
            message: Dicionário com as chaves 'type' e 'data'.
        """
        if not isinstance(message, dict):
            return

        type = message.get("type")
        data = message.get("data", {})

        if not isinstance(data, dict):
            data = {}

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

        Executa a decodificação em thread separada via run_in_executor
        para não bloquear o event loop do asyncio.

        Args:
            data: Dicionário contendo a imagem codificada em Base64 sob a chave 'image'.
        """
        image_b64 = data.get("image")
        if not image_b64:
            return

        loop = asyncio.get_event_loop()
        frame = await loop.run_in_executor(None, self._decode_frame, image_b64)

        if frame is not None:
            self._robot.push_frame(frame)

    @staticmethod
    def _decode_frame(image_b64: str):
        """ Decodifica uma imagem Base64 em um frame OpenCV (síncrono, roda fora do event loop).
        """
        try:
            frame_bytes = base64.b64decode(image_b64)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            return cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"[HANDLER] Erro ao decodificar frame: {e}")
            return None


    async def handle_ask(self, data: dict):
        """ Processa uma pergunta do visitante e envia a resposta ao tablet.

        Ignorada se o robô não estiver em um estado receptivo.
        Transiciona para THINKING durante o processamento e SPEAKING ao responder.

        Args:
            data: Dicionário contendo o texto da pergunta sob a chave 'text'.
        """
        robot_state = self._robot.get_current_state()
        ask: str = data.get("text", "")
        if not ask:
            return

        activation_words = ["oi robo", "oi robô", "ei robo", "ei robô"]

        if robot_state not in [RobotState.WAITING, RobotState.SLEEPING, RobotState.GREETING]:
            return

        if robot_state in [RobotState.SLEEPING, RobotState.GREETING]:
            if not any(word in ask.lower() for word in activation_words):
                return

        print("[SERVER] Pergunta recebida:", ask)
        await self.change_state(RobotState.THINKING)

        answer = await self._robot.send_ask(ask)
        await self._safe_send({
            "type": "answer",
            "data": { "text": answer if answer is not None else "error"}
        })

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

        Gerencia o timer de inatividade conforme o novo estado:
        - GREETING / WAITING: reinicia o timer com IDLE_TIMEOUT (30s) para SLEEPING.
        - THINKING / SPEAKING: reinicia o timer com BUSY_TIMEOUT (60s) para SLEEPING.
        - SLEEPING: cancela o timer e reinicia a interação (limpando histórico e encoding).

        Args:
            state: Novo estado a ser aplicado.
        """
        if self._disposed:
            return

        print(f"[HANDLER] Estado alterado de _{self._robot.get_current_state().value}_ para _{state.value}_")
        self._robot.set_state(state)

        # Envia o novo estado através do WebSocket de forma segura
        await self._safe_send({
            "type": "state",
            "data": { 
                "value": state.value 
            }
        })

        if state in [RobotState.GREETING, RobotState.WAITING]:
            self._reset_sleep_timer(IDLE_TIMEOUT)
        elif state in [RobotState.THINKING, RobotState.SPEAKING]:
            self._reset_sleep_timer(BUSY_TIMEOUT)
        elif state == RobotState.SLEEPING:
            self._cancel_sleep_timer()
            self._robot.reset_interaction()


    async def on_face_detected(self):
        """ Callback acionado pelo Robot ao detectar um rosto.

        Transiciona para GREETING apenas se o robô estiver em SLEEPING,
        evitando reinicializações durante interações ativas.
        """
        if self._disposed:
            return

        if self._robot.get_current_state() == RobotState.SLEEPING:
            await self.change_state(RobotState.GREETING)


    def _reset_sleep_timer(self, timeout: int = IDLE_TIMEOUT) -> None:
        """ Cancela o timer atual e inicia um novo com a duração especificada.

        Args:
            timeout: Duração em segundos antes de transicionar para SLEEPING.
        """
        self._cancel_sleep_timer()
        self._sleep_task = asyncio.create_task(self._sleep_timeout(timeout))


    def _cancel_sleep_timer(self) -> None:
        """ Cancela o timer de inatividade se estiver ativo.
        """
        if self._sleep_task and not self._sleep_task.done():
            current_task = asyncio.current_task()
            if self._sleep_task is not current_task:
                self._sleep_task.cancel()
        self._sleep_task = None


    async def _sleep_timeout(self, timeout: int) -> None:
        """ Aguarda o tempo configurado e transiciona o robô para SLEEPING.
        
        Cancelada automaticamente ao mudar de estado ou resetar o timer.

        Args:
            timeout: Duração em segundos da espera.
        """
        try:
            await asyncio.sleep(timeout)
            self._sleep_task = None
            print(f"[HANDLER] Timeout atingido ({timeout}s). Indo para SLEEPING.")
            await self.change_state(RobotState.SLEEPING)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[HANDLER] Erro no timeout de inatividade: {e}")