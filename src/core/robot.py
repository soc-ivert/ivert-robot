from src.storage.database import Database
from src.vision.face_detector import FaceDetector
from src.ai.agent import Agent
from src.ai.tools import create_tools

class Robot():

    def __init__(self):
        self._db = Database()
        self._face_detector = FaceDetector()
        self._agent = Agent(tools=create_tools(self._db, self._face_detector))