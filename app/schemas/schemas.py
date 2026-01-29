from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.models import JobStatus, UserType


# Comentário (pt-BR):
# Este módulo contém os modelos Pydantic usados para entrada (Create)
# e saída (Read) da API. Mantemos esta camada separada da camada ORM
# para evitar expor diretamente os modelos de banco de dados.


class UserBase(BaseModel):
    """Common fields shared across User schemas."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    phone_number: str
    user_type: UserType
    full_name: str
    latitude: float | None = None
    longitude: float | None = None


class UserCreate(UserBase):
    """
    Schema para criação de usuários.

    Comentário (pt-BR):
    Este modelo representa os dados que esperamos receber do cliente
    quando um novo usuário é registrado no sistema.
    """

    # Nenhum campo extra por enquanto; podemos evoluir depois (ex.: senha, skills).
    pass


class UserRead(UserBase):
    """
    Schema para leitura de usuários (respostas da API).

    Comentário (pt-BR):
    Inclui campos adicionais somente disponíveis após o usuário existir
    no banco (id, estágio de conversa).
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,  # Permite criar o schema a partir de objetos ORM.
    )

    id: int
    conversation_stage: str


class JobOpportunityBase(BaseModel):
    """Common fields shared across JobOpportunity schemas."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    title: str
    description: str
    payment_offer: float
    latitude: float
    longitude: float


class JobOpportunityCreate(JobOpportunityBase):
    """
    Schema para criação de oportunidades de trabalho.
    """

    contractor_id: int


class JobOpportunityRead(JobOpportunityBase):
    """
    Schema para leitura de oportunidades de trabalho.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
    )

    id: int
    contractor_id: int
    status: JobStatus
    created_at: datetime

