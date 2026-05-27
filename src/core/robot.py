from src.storage.database import Database
from src.vision.face_detector import FaceDetector
from src.ai.agent import Agent
from src.ai.tools import create_tools

class Robot():

    def __init__(self, camera_source = None):
        self._db = Database()
        self._detector = FaceDetector(camera_source)
        self._agent = Agent(tools=create_tools(self._db, self._detector))

    def push_frame(self, frame):
        self._detector.push_frame(frame)

    def run(self):
        
        self._detector.start_detection()
        
        while True:
            ask = input("Ask: ")
            answer = self._agent.send(ask)
            print(answer)