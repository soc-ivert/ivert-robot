import sqlite3
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    name: str
    contact: str  # e-mail ou telefone
    encoding: np.ndarray  # gerado por face_recognition.face_encodings()
    id: Optional[int] = field(default=None)

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', contact='{self.contact}')"


class Database:
    '''
    Gerencia a persistência de usuários com reconhecimento facial em SQLite.

    Tabela: users
        id       INTEGER PRIMARY KEY AUTOINCREMENT
        name     TEXT    NOT NULL
        contact  TEXT    NOT NULL  (e-mail ou telefone)
        encoding BLOB    NOT NULL  (ndarray float64 serializado via tobytes/frombuffer)

    Busca por encoding:
        Como encodings faciais nunca são exatamente iguais entre fotos
        distintas, a busca retorna o usuário mais próximo (distância
        euclidiana) cujo encoding seja menor que `tolerance` (padrão 0.6,
        mesmo valor usado pela lib face_recognition).
    '''

    def __init__(self, db_path: str = "data/bot.db", tolerance: float = 0.6) -> None:
        self._db_path = db_path
        self.tolerance = tolerance
        self._create_table()

    def _connect(self) -> sqlite3.Connection:

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row  # acesso por nome de coluna

        return conn

    def _create_table(self) -> None:

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
        return encoding.astype(np.float64).tobytes()

    @staticmethod
    def _bytes_to_ndarray(data: bytes) -> np.ndarray:
        return np.frombuffer(data, dtype=np.float64)

    def _row_to_user(self, row: sqlite3.Row) -> User:
        ''' Transforma uma linha da tabela em um objeto User.
        '''

        return User(
            id=row["id"],
            name=row["name"],
            contact=row["contact"],
            encoding=self._bytes_to_ndarray(row["encoding"]),
        )

    def insert(self, user: User) -> User:
        '''
        Insere um novo usuário no banco.
        Retorna o mesmo User com o campo `id` preenchido.
        ''' 

        sql = "INSERT INTO users (name, contact, encoding) VALUES (?, ?, ?)"

        with self._connect() as conn:
            cursor = conn.execute(
                sql,
                (user.name, user.contact, self._ndarray_to_bytes(user.encoding)),
            )
            user.id = cursor.lastrowid

        return user

    def search_by(self, column: str, value: object) -> list[User]:
        '''
        Retorna usuários com base em uma coluna ou pelo encoding facial.

        Colunas com correspondência exata: 'id', 'name', 'contact'
            db.search_by("name", "Maria")
            db.search_by("contact", "maria@email.com")

        Busca por proximidade facial: 'encoding'
            db.search_by("encoding", encoding_ndarray)
            Retorna os usuários cujo encoding tem distância euclidiana
            menor que `self.tolerance`, ordenados do mais próximo ao
            mais distante. Retorna lista vazia se nenhum corresponder.
        '''
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
        '''
        Carrega todos os encodings do banco e retorna os usuários dentro
        da tolerância, ordenados por distância crescente.

        A distância euclidiana é equivalente ao que face_recognition usa
        internamente em face_recognition.compare_faces().
        '''

        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()

        if not rows:
            return []

        users = [self._row_to_user(row) for row in rows]
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
        ''' Retorna todos os usuários cadastrados na tabela users.
        '''

        sql = "SELECT * FROM users"

        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()

        return [self._row_to_user(row) for row in rows]