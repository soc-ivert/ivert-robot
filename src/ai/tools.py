from src.storage.database import Database, User
from src.vision.face_detector import FaceDetector
import random

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
        print("[TOOLS] Chamada a check_face()")

        encoding = face_detector.get_current_encoding()

        if encoding is None:
            print(f"[TOOLS] Nenhum rosto encontrado na chamada a check_face")
            return "Nenhum rosto detectado na câmera"
        
        result = db.search_by(column="encoding",value=encoding) 

        if result:
            print(f"[TOOLS] check_face retornando {result[0].name}")
            return result[0].name
        else:
            print(f"[TOOLS] check_face retornando Desconhecido")
            return "Desconhecido"

    def signup(name: str) -> bool:
        """ Cadastra a pessoa atualmente visível na câmera no banco de dados.
        
        Execute esta ferramenta SOMENTE quando o usuário demonstrar a intenção explícita de se cadastrar 
        ou após ele confirmar a oferta de cadastro. É necessário coletar somente o nome da pessoa antes 
        de chamar esta função.

        Args:
            name: O nome do usuário a ser cadatrado.

        Returns:
            bool: True se o cadastro foi realizado com sucesso. 
                  False se falhar (geralmente porque nenhum rosto foi detectado ou posicionado corretamente na câmera).
        """

        try:
            encoding = face_detector.get_current_encoding()

            if encoding is None:
                print("[TOOLS] Nenhum encoding detectado.")
                return False

            user = db.insert(User(name=name, encoding=encoding))
            print(f"[TOOLS] Cadastrado com sucesso no banco: {user}")
            return True

        except Exception as e:
            print(f"[TOOLS] Erro em signup: {e}")
            return False

            
    return [signup, check_face]