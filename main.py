from fastapi import FastAPI

from app.routers.webhook import router as webhook_router
from app.core.config import settings  # noqa: F401  # Import ensures .env is loaded at startup
from app.core.database import Base, engine
from app.models import models as models_module  # noqa: F401  # Import registers ORM models


# Comentário (pt-BR):
# Este arquivo é o ponto de entrada da aplicação FastAPI.
# Aqui criamos a instância principal do app e registramos os routers
# que expõem as rotas HTTP (por exemplo, o /webhook usado pelo WhatsApp/Twilio).

app = FastAPI(
    title="Contech WhatsApp Bot",
    description=(
        "Backend em FastAPI para um bot de WhatsApp focado na construção civil. "
        "Este serviço será integrado ao Twilio para receber e enviar mensagens."
    ),
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    """
    Application startup hook.

    Comentário (pt-BR):
    No startup da aplicação criamos automaticamente as tabelas no banco de dados,
    usando o metadata do SQLAlchemy. Em ambientes de produção, você provavelmente
    usaria migrações (ex.: Alembic), mas para desenvolvimento este approach é prático.
    """

    Base.metadata.create_all(bind=engine)


# Comentário (pt-BR):
# Registramos o router responsável pelas rotas de integração com o WhatsApp/Twilio.
# Ao usar um prefixo (por exemplo, /webhook), mantemos a organização das rotas.
app.include_router(webhook_router, prefix="")


@app.get("/health", tags=["healthcheck"])
async def healthcheck() -> dict[str, str]:
    """
    Simple health-check endpoint.

    Returns:
        A small JSON payload indicating the service is alive.
    """

    # Comentário (pt-BR):
    # Endpoint simples para verificar se a API está no ar.
    # Útil para monitoramento e testes rápidos.
    return {"status": "ok"}


# Comentário (pt-BR):
# Para rodar a aplicação localmente você pode usar uvicorn diretamente:
#   uvicorn main:app --reload
# Em produção no Render, é recomendado usar gunicorn com worker Uvicorn:
#   gunicorn -k uvicorn.workers.UvicornWorker main:app
#
# A variável de ambiente PORT (fornecida pelo Render) é usada abaixo
# apenas quando rodamos o arquivo diretamente com `python main.py`.

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

