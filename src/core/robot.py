from src.storage.database import Database
from src.vision.face_detector import FaceDetector
from src.ai.agent import Agent
from src.ai.tools import create_tools

class Robot():
    """ Classe controladora que orquestra as operações do Robô IVERT.

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

    def start(self):
        """ Inicia detecção/processamento de imagens do detector.
        """
        self._detector.start_detection()

    def push_frame(self, frame):
        """ Permite injetar frames no detector para que ele apenas os processe.

        Deve ser chamado continuamente dentro do loop principal de captura de vídeo.

        Args:
            frame (numpy.ndarray): O frame da imagem capturada.
        """
        self._detector.push_frame(frame)

    def send_ask(self, ask:str) -> str | None:
        """ Envia uma mensagem para o agente de IA do robô e obtém a resposta.

        Envia o input do usuário para o chat contextual do agente, acionando
        as ferramentas do agente se a IA julgar necessário.

        Args:
            ask: A frase, pergunta ou comando dito/digitado pelo usuário.

        Returns:
            str: A resposta textual gerada pelo robô.
            None: Caso ocorra alguma falha.
        """
        return self._agent.send(ask)