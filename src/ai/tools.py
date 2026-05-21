from src.storage.database import Database, User
from src.vision.face_detector import FaceDetector
import random

NAME_MOCK = ["Vini", "Helen", "João", "Bruno", "Carla", "Diego", "Helena"]

def create_tools(db: Database, face_detector: FaceDetector):

    def check_face() -> str:
        """
        """
        encoding = face_detector.current_face_encoding

        if encoding is None:
            return "Nenhum rosto detectado na câmera"
        
        result = db.search_by(column="encoding",value=encoding) 
        return result[0].name if result else "Desconhecido"
                                                          
    def signup() -> bool:
        """
        """
        encoding = face_detector.current_face_encoding

        if encoding is None:
            return False

        name = random.choice(NAME_MOCK)
        db.insert(User(name, f"{name}@email.com", face_detector.current_face_encoding))
        return True
    
    return [signup, check_face]