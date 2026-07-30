from google import genai
from google.genai import types
from pathlib import Path
from src.exceptions import AgentError, ChatCreationError, SystemPromptError
import os

MODEL = "gemini-2.5-flash-lite"

class Agent():
    """ Agente de IA baseado na API do Google Gemini.

    Gerencia a comunicação com o modelo Gemini, lidando com a inicialização do cliente, 
    carregamento de prompts do sistema, gerenciamento de histórico de conversas e execução de ferramentas (tools).

    Attributes:
        _MAX_MESSAGES (int): Número máximo de mensagens mantidas no histórico do chat.
    """

    _MAX_MESSAGES = 16

    def __init__(self, tools: list):
        """ Inicializa o Agente de IA.

        Args:
            tools: Lista de ferramentas (funções) que o agente pode executar.

        Raises:
            AgentError: Se ocorrer qualquer erro durante a inicialização do agente ou subcomponentes.
        """

        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise AgentError("Variável de ambiente GEMINI_API_KEY não configurada no env")
            self._client = genai.Client(api_key=api_key)
            self._tools = tools
            self._prompts = self._load_prompts()
            self._chat = self._create_chat()

        except AgentError:
            raise
        except Exception:
            raise AgentError("Erro ao iniciar o agente de IA.")


    def _load_prompts(self):
        """ Carrega e consolida os arquivos de prompt do sistema.

        Lê os arquivos de configuração contidos no diretório de prompts e os estrutura em um objeto de conteúdo 
        adequado para as instruções do sistema do Gemini.

        Returns:
            types.Content: Objeto estruturado contendo as instruções do sistema divididas em partes.

        Raises:
            SystemPromptError: Se houver falha na leitura ou localização dos arquivos de prompt.
        """

        # Caminho do diretório contendo os prompts do sistema
        prompts_dir = Path(__file__).parent / "prompts"

        try:
            parts_list = []
        
            for file_path in sorted(prompts_dir.iterdir()):
                if file_path.is_file():
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        parts_list.append(types.Part.from_text(text=content))

            if not parts_list:
                raise SystemPromptError("Nenhum arquivo de prompt encontrado.")

            prompts = types.Content(
                role="system",
                parts=parts_list
            )
            
            return prompts
        
        except Exception:
            raise SystemPromptError("Erro ao ler arquivos de prompt.")


    def _create_chat(self):
        """Cria uma nova sessão de chat com o Gemini.

        Returns:
            Uma nova instância de sessão de chat do Gemini.

        Raises:
            ChatCreationError: Se falhar ao criar o chat.
        """
        try:
            return self._client.aio.chats.create(
                model=MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=self._prompts,
                    tools=self._tools,
                ),
            )
        except Exception:
            raise ChatCreationError("Erro ao criar uma sessão de chat.")

 
    def reset(self) -> bool:
        """Reinicia a conversa atual limpando todo o histórico do chat.

        Returns:
            bool: True se o chat foi reiniciado com sucesso, False caso contrário.
        """
        try:
            self._chat = self._create_chat()
            return True
        except ChatCreationError:
            return False
 
    async def send(self, user_input: str) -> str | None:
        """ Envia uma mensagem do usuário para o agente.

        Também monitora o tamanho do histórico. Caso exceda o limite definido em `_MAX_MESSAGES`, 
        as mensagens mais antigas são apagadas para otimizar o uso de tokens e contexto.

        Args:
            user_input: O texto ou pergunta enviado pelo usuário.

        Returns:
            str: A resposta em texto gerada pelo Gemini.
            None: Se ocorrer um erro durante o envio ou geração da resposta.
        """

        # Verifica o tamanho do histórico para limitar o contexto.
        if len(self._chat.get_history()) > self._MAX_MESSAGES:
            self._chat.history = self._chat.get_history()[-self._MAX_MESSAGES:]

        try:
            response = await self._chat.send_message(user_input)
            return response.text
        except Exception as e:
            print("[AGENT] Erro:", e)
            return None