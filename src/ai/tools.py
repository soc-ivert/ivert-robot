from src.storage.database import Database, User
from src.vision.face_detector import FaceDetector
import random

NAME_MOCK = ["Vini", "Helen", "João", "Bruno", "Carla", "Diego", "Helena"]

def create_tools(db: Database, face_detector: FaceDetector):

    def check_face() -> str:
        """ Verifica se a pessoa visível na câmera já é conhecida no sistema.
        
        Execute esta ferramenta imediatamente no início de qualquer interação para identificar o usuário. 
        O retorno indicará o nome da pessoa ou se ela ainda não foi cadastrada.

        Returns:
            str: O nome da pessoa caso ela seja conhecida; 
                 "Desconhecido" se a pessoa não possuir cadastro;
                 "Nenhum rosto detectado na câmera" se não houver ninguém visível.
        """
        encoding = face_detector.current_face_encoding

        if encoding is None:
            return "Nenhum rosto detectado na câmera"
        
        result = db.search_by(column="encoding",value=encoding) 
        return result[0].name if result else "Desconhecido"
                                                          
    def signup() -> bool: # TODO criar fluxo de cadastro e remover mocks para teste
        """ Cadastra a pessoa atualmente visível na câmera no banco de dados.
        
        Execute esta ferramenta SOMENTE quando o usuário demonstrar a intenção explícita de se cadastrar 
        ou após ele confirmar a oferta de cadastro. Não é necessário coletar dados como nome ou e-mail do 
        usuário antes de chamar esta função, pois os dados são obtidos de forma automatizada.

        Returns:
            bool: True se o cadastro foi realizado com sucesso. 
                  False se falhar (geralmente porque nenhum rosto foi detectado ou posicionado corretamente na câmera).
        """
        encoding = face_detector.current_face_encoding

        if encoding is None:
            return False

        name = random.choice(NAME_MOCK)
        db.insert(User(name, f"{name}@email.com", face_detector.current_face_encoding))
        return True
    
    return [signup, check_face]