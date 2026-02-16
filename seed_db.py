"""
Simple database seeding script for local development.

Comentário (pt-BR):
Este script popula o banco SQLite (construction.db) com dados de teste,
incluindo um usuário do tipo CONSTRUTORA e algumas vagas de trabalho
em São José dos Campos.
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models.models import Base, JobOpportunity, JobStatus, User, UserType


def seed_data() -> None:
    """
    Populate the database with initial test data.
    """

    # Garante que as tabelas existam antes de qualquer operação (Postgres/AWS).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Verifica se já existem usuários.
        existing_user = db.scalars(select(User)).first()

        if existing_user is None:
            # Cria 1 usuário CONSTRUTORA (dono da obra).
            contractor = User(
                phone_number="whatsapp:+5511999990000",
                user_type=UserType.CONTRACTOR,
                full_name="Construtora Exemplo LTDA",
                latitude=-23.2237,
                longitude=-45.9009,
                conversation_stage="MAIN_MENU",
            )
            db.add(contractor)
            db.commit()
            db.refresh(contractor)
        else:
            contractor = existing_user

        # Verifica se já existem vagas para evitar duplicação em múltiplas execuções.
        existing_job = db.scalars(select(JobOpportunity)).first()

        if existing_job is None:
            # Coordenadas próximas ao centro de São José dos Campos.
            sjc_lat, sjc_lon = -23.2237, -45.9009

            jobs = [
                JobOpportunity(
                    title="Pedreiro para Reboco",
                    description="Serviço de reboco em parede interna de prédio residencial.",
                    payment_offer=250.0,
                    latitude=sjc_lat + 0.005,
                    longitude=sjc_lon + 0.005,
                    contractor_id=contractor.id,
                    status=JobStatus.OPEN,
                ),
                JobOpportunity(
                    title="Eletricista Predial",
                    description="Instalação de fiação elétrica em edifício comercial.",
                    payment_offer=300.0,
                    latitude=sjc_lat - 0.004,
                    longitude=sjc_lon + 0.003,
                    contractor_id=contractor.id,
                    status=JobStatus.OPEN,
                ),
                JobOpportunity(
                    title="Pintura Fachada",
                    description="Pintura de fachada de prédio de 5 andares.",
                    payment_offer=400.0,
                    latitude=sjc_lat + 0.002,
                    longitude=sjc_lon - 0.004,
                    contractor_id=contractor.id,
                    status=JobStatus.OPEN,
                ),
            ]

            db.add_all(jobs)
            db.commit()

        print("Banco de dados populado com sucesso!")

    except Exception as exc:  # pragma: no cover - defensive guard
        # Comentário (pt-BR):
        # Em caso de erro, fazemos rollback para não deixar transações pela metade.
        db.rollback()
        print("Erro ao popular o banco de dados:", repr(exc))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
