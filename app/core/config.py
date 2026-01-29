import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict


# Comentário (pt-BR):
# Este módulo centraliza a configuração da aplicação.
# Utilizamos python-dotenv para carregar variáveis de ambiente do arquivo .env
# e Pydantic para ter um modelo de configuração tipado e validado.


# Carrega variáveis de ambiente do arquivo .env localizado na raiz do projeto.
# Se o arquivo não existir, load_dotenv simplesmente não faz nada.
load_dotenv()


class Settings(BaseModel):
    """
    Strongly-typed application settings.

    This model reads process environment variables and exposes them in a
    structured way to the rest of the application.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    # Comentário (pt-BR):
    # Aqui definimos apenas algumas variáveis principais.
    # Você pode expandir conforme o projeto crescer.

    # Ambiente de execução (ex.: "dev", "prod")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # URL do banco de dados.
    # Comentário (pt-BR):
    # Em produção (Render), você pode definir DATABASE_URL apontando para PostgreSQL.
    # Em desenvolvimento, usamos por padrão um SQLite local.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./construction.db")

    # Configurações relacionadas ao Twilio
    TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str | None = os.getenv("TWILIO_WHATSAPP_NUMBER")



def _build_settings() -> Settings:
    """
    Internal helper to instantiate Settings with defensive error handling.

    Returns:
        A Settings instance loaded from environment variables.
    """

    # Comentário (pt-BR):
    # Esta função encapsula a criação do objeto de configuração.
    # Caso algo dê errado, podemos capturar e logar de forma centralizada.
    try:
        return Settings()
    except Exception as exc:  # pragma: no cover - defensive guard
        # Em um projeto real, você provavelmente usaria um logger estruturado.
        # Aqui usamos print apenas para ilustrar.
        print("Erro ao carregar configurações da aplicação:", repr(exc))
        # Re-raise para falhar rápido, já que sem configuração válida a app não deve subir.
        raise


# Instância global de configurações utilizada pelo resto da aplicação.
# Comentário (pt-BR):
# Ter um único objeto de Settings evita leituras diretas de os.getenv espalhadas pelo código,
# mantendo a configuração centralizada e mais fácil de manter.
settings: Settings = _build_settings()


def get_settings() -> Settings:
    """
    Public accessor for application settings.

    Using a function allows us to later integrate with dependency injection
    or override configuration in tests if needed.
    """

    return settings

