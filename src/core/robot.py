from src.storage.database import Database
from src.vision.face_detector import FaceDetector
from src.ai.agent import Agent
from src.ai.tools import create_tools
from src.core.enums import RobotState

import asyncio

class Robot():
    """ Classe controladora que orquestra as operações do Robô.

    Esta classe atua como o ponto central do sistema, integrando o banco de 
    dados local, o detector facial e o agente de inteligência artificial.
    """

    def __init__(self, camera_source = None):
        """ Inicializa o Robô e configura todos os seus subsistemas.

        Args:
            camera_source (int | str | None): O índice da câmera (ex: 0) ou o caminho
            de um arquivo/fluxo de vídeo. O padrão é None (usa a câmera padrão).
        """
        self._db = Database()
        self._detector = FaceDetector(camera_source)
        self._agent = Agent(tools=create_tools(self._db, self._detector))
        self._state = RobotState.SLEEPING
        self._loop = None
        self._on_face_detected = None

    def start(self):
        """ Inicializa componentes do robô.
        """
        self._loop = asyncio.get_event_loop()
        self._detector.set_face_callback(self._handle_face_detected)
        self._detector.start_detection()

    def push_frame(self, frame):
        """ Permite injetar frames no detector para que ele apenas os processe.

        Deve ser chamado continuamente dentro do loop principal de captura de vídeo.

        Args:
            frame (numpy.ndarray): O frame da imagem capturada.
        """
        self._detector.push_frame(frame)

    async def send_ask(self, ask:str) -> str | None:
        """ Envia uma mensagem para o agente de IA do robô e obtém a resposta.

        Envia o input do usuário para o chat contextual do agente, acionando
        as ferramentas do agente se a IA julgar necessário.

        Args:
            ask: A frase, pergunta ou comando dito/digitado pelo usuário.

        Returns:
            str: A resposta textual gerada pelo robô.
            None: Caso ocorra alguma falha.
        """
        return await self._agent.send(ask)

    def reset_interaction(self) -> bool:
        """ Reinicia a conversa atual limpando todo o histórico do chat juntamente ao encoding armazenado.
    
        Significa uma nova interação iniciando
            
        Returns:
            bool: True se o chat foi reiniciado com sucesso, False caso contrário.
        """
        self._detector.clear_encoding()
        return self._agent.reset()

    def set_state(self, state: RobotState):
        """ Altera o estado atual do robô.

        Args:
            RobotState: O novo estado.
        """
        self._state = state
        
    def get_current_state(self):
        """ Obtem o estado atual do robô.
        """
        return self._state
    
    def set_face_callback(self, callback):
        """ Registra o callback a ser invocado quando o detector identificar um rosto.

        Args:
            callback: Função assíncrona a ser agendada no event loop ao detectar um rosto.
        """
        self._on_face_detected = callback

    def _handle_face_detected(self):
        """ Ponte entre a thread do FaceDetector e o event loop do asyncio.

        Chamada diretamente pela thread do detector. Agenda o callback assíncrono
        registrado via `set_face_callback` no event loop do uvicorn, garantindo
        que a execução ocorra no contexto correto.
        """
        if self._on_face_detected and self._loop:
            self._loop.call_soon_threadsafe(asyncio.ensure_future, self._on_face_detected())