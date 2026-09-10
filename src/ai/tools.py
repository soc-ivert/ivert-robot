from src.storage.database import Database, User
from src.vision.face_detector import FaceDetector
import csv
import io
import json
import time
from pathlib import Path
import requests

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQwcJ1NL-CRep3M2o4-qEjkzmpZJ12XwQUo4tXf7GBcdYh_iTCrEUCvMWWn63XeNGbm7EN309dxkz22/pub?gid=0&single=true&output=csv"

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


    def get_eventos() -> list[dict]:
        """ Obtém a lista de eventos ativos do instituto.

        Returns:
            list[dict]: Lista de eventos, cada um como um dicionário com as colunas da planilha. 
            Retorna uma Lista vazia se nenhum evento estiver disponível.
        """
        cache_path = Path("data/events.json")
        ttl_seconds = 24 * 60 * 60

        cache = None
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                cache = None

        if cache and (time.time() - cache["timestamp"]) < ttl_seconds:
            print("[TOOLS] get_eventos retornando do cache")
            return cache["eventos"]

        try:
            response = requests.get(CSV_URL, timeout=8)
            response.raise_for_status()
            reader = csv.DictReader(io.StringIO(response.text))
            eventos = [dict(row) for row in reader]
        except Exception as e:
            print(f"[TOOLS] Falha ao buscar eventos, usando cache existente: {e}")
            return cache["eventos"] if cache else []

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump({"eventos": eventos, "timestamp": time.time()}, f, ensure_ascii=False, indent=2)

        print(f"[TOOLS] get_eventos retornando {len(eventos)} eventos da planilha")
        return eventos
            
    return [signup, check_face, get_eventos]