from google import genai
from google.genai import types
from pathlib import Path

API_KEY = ""
MODEL = "gemini-2.5-flash-lite"

class Agent():
 
    _MAX_MESSAGES = 16

    def __init__(self, tools: list):
        self._client = genai.Client(api_key=API_KEY)
        self._tools = tools
        self._prompts = self._load_prompts()
        self._chat = self._create_chat()
 
    # TODO Ler toda a pasta prompts, sem especificar nomes
    def _load_prompts(self):

        base_path = Path(__file__).parent

        with open(base_path / "prompts" / "sys_prompt.md", "r", encoding="utf-8") as f:
            sys_prompt = f.read()

        with open(base_path / "prompts" / "ivert_data.md", "r", encoding="utf-8") as f:
            ivert_infos = f.read()

        with open(base_path / "prompts" / "ivert_events.csv", "r", encoding="utf-8") as f:
            ivert_events = f.read()

        prompts = types.Content(
            role="system",
            parts=[
                types.Part.from_text(text=sys_prompt),
                types.Part.from_text(text=ivert_infos),
                types.Part.from_text(text=ivert_events)
            ]
        )

        return prompts

    def _create_chat(self):
        """ Cria uma nova sessão de chat com o Gemini.
        """
        return self._client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=self._prompts,
                tools=self._tools,
            ),
        )
 
    def reset(self):
        """ Inicia uma nova sessão, reinicinado a conversa e limpando o histórico.
        """
        self._chat = self._create_chat()
 
    def send(self, user_input: str) -> str:
        """ Envia uma mensagem e retorna a resposta em texto.
        """

        if len(self._chat.get_history()) > self._MAX_MESSAGES:
            self._chat.history = self._chat.get_history()[-self._MAX_MESSAGES:]

        response = self._chat.send_message(user_input)
        return response.text