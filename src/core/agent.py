from google import genai
from google.genai import types
from src.core.tools import *

API_KEY = ""
MODEL = "gemini-2.5-flash-lite"
SYSTEM_PROMPT = "Você é um agente do Ivert, uma casa de cultura"
TOOLS = [start_signup, check_face]

class Agent:
 
    _MAX_MESSAGES = 16

    def __init__(self):
        self._client = genai.Client(api_key=API_KEY)
        self._chat = self._create_chat()
 
    def _create_chat(self):
        """ Cria uma nova sessão de chat com o Gemini.
        """
        return self._client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=TOOLS,
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