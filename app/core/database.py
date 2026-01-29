from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings


# Comentário (pt-BR):
# Este módulo define a camada básica de acesso a dados usando SQLAlchemy 2.0.
# Aqui configuramos a engine (conexão com o banco), a fábrica de sessões
# e a função de dependência get_db para ser usada nos endpoints FastAPI.


settings = get_settings()


# URL do banco de dados.
# Comentário (pt-BR):
# Em produção, DATABASE_URL pode apontar para PostgreSQL.
# Em desenvolvimento, o valor padrão é um SQLite local (definido em Settings).
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


# create_engine é o ponto central de conexão com o banco.
# Para SQLite, o parâmetro check_same_thread=False é necessário quando usado com FastAPI/Uvicorn.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
    future=True,
)


# Declarative Base usada por todos os modelos ORM.
Base = declarative_base()


# Fábrica de sessões.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Yields:
        An active SQLAlchemy Session instance.

    Comentário (pt-BR):
    Esta função é usada como dependência nos endpoints FastAPI.
    Ela garante que a sessão com o banco seja aberta no início da
    requisição e fechada corretamente ao final, mesmo em caso de erro.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
