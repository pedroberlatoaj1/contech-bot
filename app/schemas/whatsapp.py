from pydantic import BaseModel, ConfigDict


# Comentário (pt-BR):
# Este módulo contém os "schemas" Pydantic responsáveis por validar
# a estrutura dos dados recebidos e enviados pelo bot via WhatsApp/Twilio.
# Mantemos estes modelos separados para favorecer reuso e clareza.


class WhatsAppIncomingMessage(BaseModel):
    """
    Schema representing the minimal fields of an incoming WhatsApp message
    as sent (or adapted) by Twilio.
    """

    model_config = ConfigDict(
        strict=True,
        extra="ignore",
        populate_by_name=True,
    )

    # Comentário (pt-BR):
    # Estes campos representam um subconjunto simples do payload do Twilio.
    # Em produção, você provavelmente adicionaria vários outros campos.

    from_number: str
    """E.164 phone number of the sender (WhatsApp user)."""

    to_number: str
    """E.164 phone number of the bot/WhatsApp business number."""

    message_body: str
    """Raw text body of the incoming message."""


class WhatsAppSimpleResponse(BaseModel):
    """
    Schema for a very simple JSON response returned by our webhook.
    """

    model_config = ConfigDict(
        strict=True,
        extra="ignore",
    )

    message: str
    """Human-readable message to be logged or inspected in tests."""

