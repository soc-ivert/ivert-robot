import sqlite3
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    """ Representação de um usuário.

    Attributes:
        name (str): Nome completo.
        contact (str): Informação de contato, e-mail ou telefone.
        encoding (np.ndarray): Vetor de características faciais.
        id (Optional[int]): gerado automaticamente pelo banco de dados SQLite.
    """

    name: str
    contact: str  # e-mail ou telefone
    encoding: np.ndarray  # gerado por face_recognition.face_encodings()
    id: Optional[int] = field(default=None)

    def __repr__(self) -> str:
        """ Retorna uma representação string do objeto User.
        """
        return f"User(id={self.id}, name='{self.name}', contact='{self.contact}')"


class Database:
    """ Gerencia a persistência de usuários com reconhecimento facial em SQLite.

    Tabela: users
        id       INTEGER PRIMARY KEY AUTOINCREMENT
        name     TEXT    NOT NULL
        contact  TEXT    NOT NULL  (e-mail ou telefone)
        encoding BLOB    NOT NULL  (ndarray float64 serializado via tobytes/frombuffer)

    Busca por encoding:
        Como encodings faciais nunca são exatamente iguais entre fotos distintas, 
        a busca retorna o usuário mais próximo (distância euclidiana) cujo encoding 
        seja menor que `tolerance` (padrão 0.6, mesmo valor usado pela lib face_recognition).
    """

    def __init__(self, db_path: str = "data/bot.db", tolerance: float = 0.6) -> None:
        """ Inicializa o gerenciador de banco de dados e cria a estrutura necessária.

        Args:
            db_path: Caminho do arquivo de banco de dados. O padrão é "data/bot.db".
            tolerance: Limiar de distância euclidiana para o reconhecimento facial.
              O padrão é 0.6 (mesmo padrão adotado pela biblioteca face_recognition).
        """
        self._db_path = db_path
        self.tolerance = tolerance
        self._create_table()

    def _connect(self) -> sqlite3.Connection:
        """ Estabelece e configura uma nova conexão com o banco de dados.

        Returns:
            sqlite3.Connection: Objeto de conexão.
        """

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row  # acesso por nome de coluna

        return conn

    def _create_table(self) -> None:
        """ Cria a tabela 'users' caso ela ainda não exista no arquivo de banco.

        A tabela armazena dados textuais brutos e o vetor de características faciais
        diretamente convertido no formato binário BLOB.
        """

        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            contact  TEXT    NOT NULL,
            encoding BLOB    NOT NULL
        );
        """
        with self._connect() as conn:
            conn.execute(sql)

    # Serialização do encoding (ndarray <-> bytes)
    @staticmethod
    def _ndarray_to_bytes(encoding: np.ndarray) -> bytes:
        """ Serializa uma ndarray em um fluxo de bytes brutos (BLOB).

        Args:
            encoding: O array com as características faciais.

        Returns:
            bytes: Sequência binária correspondente.
        """
        return encoding.astype(np.float64).tobytes()

    @staticmethod
    def _bytes_to_ndarray(data: bytes) -> np.ndarray:
        """ Serializa uma ndarray em um fluxo de bytes brutos (BLOB).

        Args:
            encoding: O array com as características faciais.

        Returns:
            bytes: Sequência binária correspondente.
        """
        return np.frombuffer(data, dtype=np.float64)

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """ Converte uma linha mapeada do SQLite em uma instância de User.

        Args:
            row: Linha de dados retornada por uma consulta executada no banco.

        Returns:
            User: Objeto populado com os dados correspondentes à linha lida.
        """

        return User(
            id=row["id"],
            name=row["name"],
            contact=row["contact"],
            encoding=self._bytes_to_ndarray(row["encoding"]),
        )

    def insert(self, user: User) -> User:
        """ Insere um novo usuário no banco.
       
        Args:
            user: Uma instância da dataclass User preenchida sem o identificador id.

        Returns:
            User: A mesma instância de entrada enriquecida com o id gerado 
            automaticamente pelo banco de dados.
        """ 

        sql = "INSERT INTO users (name, contact, encoding) VALUES (?, ?, ?)"

        with self._connect() as conn:
            cursor = conn.execute(
                sql,
                (user.name, user.contact, self._ndarray_to_bytes(user.encoding)),
            )
            user.id = cursor.lastrowid

        return user

    def search_by(self, column: str, value: object) -> list[User]:
        """ Procura no banco com base em alguma coluna especificada.

        Se a coluna for 'encoding', executa uma busca avançada por proximidade vetorial.
        Para as demais colunas, realiza uma verificação direta.

        Args:
            column: O nome da coluna a ser consultada ('id', 'name', 'contact', 'encoding').
            value: O termo de busca (pode ser int, str ou um np.ndarray no caso de encoding).

        Returns:
            list[User]: Uma lista com todos os usuários encontrados. Se nenhum registro for
            localizado, retorna uma lista vazia.

        Raises:
            ValueError: Se o argumento fornecido em `column` não fizer parte dos campos 
              permitidos do banco de dados.
        """
        if column == "encoding":
            return self._search_by_encoding(value)

        allowed = {"id", "name", "contact"}

        if column not in allowed:
            raise ValueError(
                f"Coluna '{column}' não permitida. Escolha entre: {allowed | {'encoding'}}"
            )

        sql = f"SELECT * FROM users WHERE {column} = ?" 

        with self._connect() as conn:
            rows = conn.execute(sql, (value,)).fetchall()

        return [self._row_to_user(row) for row in rows]

    def _search_by_encoding(self, query: np.ndarray) -> list[User]:
        """ Compara um mapeamento facial de busca com os rostos conhecidos salvos no banco.
        
        Carrega todos os encodings do banco e retorna os usuários dentro
        da tolerância, ordenados por distância crescente.

        A distância euclidiana é equivalente ao que face_recognition usa
        internamente em face_recognition.compare_faces().

        Args:
            query: Vetor extraído do rosto atual a ser procurado.

        Returns:
            list[User]: Usuários os quais o desvio matemático está dentro do limite de 
            `tolerance`, ordenados do mais parecido ao mais distante.
        """

        users = self.get_all()
        stored = np.array([u.encoding for u in users])

        # Distância euclidiana vetorizada para todos de uma vez
        distances = np.linalg.norm(stored - query, axis=1)

        matches = [
            (user, dist)
            for user, dist in zip(users, distances)
            if dist < self.tolerance
        ]

        matches.sort(key=lambda x: x[1])

        return [user for user, _ in matches]

    def get_all(self) -> list[User]:
        """ Obtem todos os usuários registrados no banco de dados.

        Returns:
            list[User]: Lista contendo todos registros convertidos em instâncias User.
        """

        sql = "SELECT * FROM users"

        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()

        return [self._row_to_user(row) for row in rows]