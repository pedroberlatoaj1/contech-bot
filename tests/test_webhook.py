from fastapi.testclient import TestClient

from main import app


# Comentário (pt-BR):
# Estes testes são apenas um "smoke test" simples para garantir que
# a rota /webhook está registrada e responde algo, mesmo em modo inicial.


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_basic_flow(monkeypatch) -> None:
    # Comentário (pt-BR):
    # Como nossa rota /webhook exige variáveis de ambiente do Twilio,
    # usamos monkeypatch para simular estas variáveis durante o teste.

    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "test-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-token")

    form_data = {
        "From": "whatsapp:+5511999999999",
        "Body": "Olá, quero encontrar um pedreiro.",
    }

    response = client.post("/webhook", data=form_data)

    assert response.status_code == 200
    # A resposta deve ser XML do Twilio (MessagingResponse)
    assert response.headers["content-type"].startswith("application/xml")
    text = response.text
    assert "<Response>" in text and "</Response>" in text

