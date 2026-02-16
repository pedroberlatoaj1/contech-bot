from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings


# Comentário (pt-BR):
# Este módulo define a camada básica de acesso a dados usando SQLAlchemy 2.0.
# Aqui configuramos a engine (conexão com o banco), a fábrica de sessões
# e a função de dependência get_db para ser usada nos endpoints.


settings = get_settings()

# SQLAlchemy recomenda a criação de engine no nível do módulo.
# Observação: `connect_args={"check_same_thread": False}` é exclusivo do SQLite.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# SessionLocal é a fábrica de sessões. Cada request deve usar sua própria sessão.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base é a classe base para modelos declarativos.
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependência do FastAPI: fornece uma sessão de banco por request.
    Garante fechamento adequado.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
