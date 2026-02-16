from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from app.core.config import get_settings
from app.core.database import get_db
from app.core.utils import find_nearby_jobs
from app.models.models import JobOpportunity, JobStatus, User, UserType


# Comentário (pt-BR):
# Este módulo define o "router" responsável pela rota de webhook do WhatsApp.
# A ideia é que o Twilio faça uma requisição POST para este endpoint
# sempre que uma nova mensagem for recebida no número configurado.
# A resposta deve ser um XML no formato esperado pelo Twilio (MessagingResponse).


router = APIRouter(tags=["whatsapp"])


def _normalize_text(text: str) -> str:
    """
    Helper para normalizar texto livre do usuário.

    Comentário (pt-BR):
    Transformamos em minúsculas e removemos espaços extras para facilitar
    a comparação de comandos simples como "vagas", "oportunidade", etc.
    """
    return text.strip().lower()


def _build_twilio_response(message: str) -> str:
    """
    Cria um XML de resposta para o Twilio usando MessagingResponse.
    """
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)


@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),  # noqa: N803 - nome vem do Twilio
    Body: str = Form(...),  # noqa: N803 - nome vem do Twilio
    Latitude: float | None = Form(None),  # noqa: N803 - nome vem do Twilio
    Longitude: float | None = Form(None),  # noqa: N803 - nome vem do Twilio
    db: Session = Depends(get_db),
) -> Response:
    """
    WhatsApp webhook endpoint (Twilio).

    Args:
        From: Número do remetente (WhatsApp do usuário) enviado pelo Twilio.
        Body: Corpo da mensagem de texto enviada pelo usuário.
        db: Sessão de banco de dados injetada pelo FastAPI.

    Returns:
        XML com a resposta para o usuário, no formato esperado pelo Twilio.
    """
    settings = get_settings()

    # Comentário (pt-BR):
    # Exemplo defensivo: verificamos se as credenciais do Twilio
    # foram configuradas. Em produção, isso provavelmente seria
    # feito no startup da aplicação, falhando cedo caso estejam ausentes.
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Configuração do Twilio ausente. Verifique as variáveis de ambiente.",
        )

    incoming_text = Body or ""
    incoming_normalized = _normalize_text(incoming_text)

    try:
        # 1) Carrega (ou cria) o usuário a partir do número de telefone.
        stmt = select(User).where(User.phone_number == From)
        user: User | None = db.scalars(stmt).first()

        if user is None:
            # Sem Usuário: criamos o registro com estágio inicial.
            # Comentário (pt-BR):
            # O tipo ainda não é conhecido; usamos um valor padrão (WORKER)
            # que será corrigido assim que o usuário escolher a opção.
            user = User(
                phone_number=From,
                user_type=UserType.WORKER,
                full_name="",
                conversation_stage="CHOOSING_TYPE",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            welcome_msg = (
                "Olá! Bem-vindo ao Contech Bot. "
                "Você busca OPORTUNIDADES ou quer CONTRATAR?"
            )
            xml = _build_twilio_response(welcome_msg)
            return Response(content=xml, media_type="application/xml")

        # 2) Atualização de geolocalização (se vier Latitude/Longitude do WhatsApp).
        if Latitude is not None and Longitude is not None:
            user.latitude = Latitude
            user.longitude = Longitude
            db.commit()
            db.refresh(user)

            msg = "Localização recebida! Agora digite VAGAS para ver obras ao seu redor."
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # BACKDOOR: mensagem exata "/admin"
        if incoming_text.strip() == "/admin":
            user.user_type = UserType.CONTRACTOR
            user.conversation_stage = "ADMIN_ADDING_JOB"
            db.commit()
            db.refresh(user)

            msg = (
                "🛠️ Modo Admin: Para criar uma nova vaga, digite o Cargo e o Valor "
                "separados por vírgula. Ex: Encanador, 150.00"
            )
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # Estágio ADMIN_ADDING_JOB
        if (user.conversation_stage or "").strip() == "ADMIN_ADDING_JOB":
            try:
                parts = [p.strip() for p in incoming_text.split(",")]
                if len(parts) != 2:
                    raise ValueError("invalid_parts")

                title = parts[0]
                payment_offer = float(parts[1])

                if not title:
                    raise ValueError("empty_title")
            except Exception:
                msg = "Formato inválido. Tente novamente: Cargo, Valor"
                xml = _build_twilio_response(msg)
                return Response(content=xml, media_type="application/xml")

            lat = user.latitude if user.latitude is not None else -23.2237
            lon = user.longitude if user.longitude is not None else -45.9009

            job = JobOpportunity(
                title=title,
                description="Vaga criada via WhatsApp (modo admin).",
                payment_offer=payment_offer,
                latitude=lat,
                longitude=lon,
                contractor_id=user.id,
                status=JobStatus.OPEN,
            )

            db.add(job)
            user.conversation_stage = "MAIN_MENU"
            db.commit()
            db.refresh(user)

            msg = (
                f"✅ Vaga de {title} cadastrada com sucesso! "
                "Ela já aparece para os trabalhadores próximos."
            )
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # 3) Máquina de estados baseada em conversation_stage.
        stage = user.conversation_stage or "NEW"

        # Estágio inicial: usuário existente mas ainda não configurado.
        if stage == "NEW":
            user.conversation_stage = "CHOOSING_TYPE"
            db.commit()
            db.refresh(user)
            msg = "Olá novamente! Você busca OPORTUNIDADES ou quer CONTRATAR?"
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # Estágio CHOOSING_TYPE
        if stage == "CHOOSING_TYPE":
            # Palavras-chave para trabalhador
            if any(
                keyword in incoming_normalized
                for keyword in (
                    "oportunidade",
                    "oportunidades",
                    "trabalhar",
                    "vaga",
                    "vagas",
                )
            ):
                user.user_type = UserType.WORKER
                user.conversation_stage = "ASKING_NAME"
                db.commit()
                db.refresh(user)

                msg = "Perfeito! Qual seu nome completo?"
                xml = _build_twilio_response(msg)
                return Response(content=xml, media_type="application/xml")

            # Palavras-chave para contratante
            if any(
                keyword in incoming_normalized
                for keyword in ("contratar", "obra", "obra nova", "contratante")
            ):
                user.user_type = UserType.CONTRACTOR
                user.conversation_stage = "ASKING_NAME"
                db.commit()
                db.refresh(user)

                msg = "Ótimo! Qual o nome completo do responsável pela contratação?"
                xml = _build_twilio_response(msg)
                return Response(content=xml, media_type="application/xml")

            # Entrada inesperada: reforça a pergunta.
            msg = (
                "Não entendi. Responda OPORTUNIDADES se você busca trabalho "
                "ou CONTRATAR se você quer encontrar profissionais."
            )
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # Estágio ASKING_NAME
        if stage == "ASKING_NAME":
            name = incoming_text.strip()

            if not name:
                msg = "Por favor, envie seu nome completo para continuar o cadastro."
                xml = _build_twilio_response(msg)
                return Response(content=xml, media_type="application/xml")

            user.full_name = name
            user.conversation_stage = "MAIN_MENU"
            db.commit()
            db.refresh(user)

            msg = "Cadastro concluído! Digite VAGAS para ver obras próximas."
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # Estágio MAIN_MENU
        if stage == "MAIN_MENU":
            if incoming_normalized == "vagas":
                # Comentário (pt-BR):
                # Agora utilizamos a geolocalização real do usuário, caso esteja disponível.
                if user.latitude is None or user.longitude is None:
                    msg = (
                        "Para encontrar obras próximas, preciso saber onde você está. "
                        "Por favor, clique no clipe (anexo) e me envie sua Localização."
                    )
                    xml = _build_twilio_response(msg)
                    return Response(content=xml, media_type="application/xml")

                jobs_stmt = select(JobOpportunity).where(
                    JobOpportunity.status == JobStatus.OPEN
                )
                jobs = db.scalars(jobs_stmt).all()

                nearby_jobs = find_nearby_jobs(
                    user_lat=user.latitude,
                    user_lon=user.longitude,
                    jobs=jobs,
                    radius_km=10.0,
                )

                if not nearby_jobs:
                    msg = "Não encontramos vagas próximas no momento. Tente novamente mais tarde."
                else:
                    lines: list[str] = ["Encontrei as seguintes vagas próximas a você:"]
                    for job in nearby_jobs:
                        lines.append(f"- {job.title} (R$ {job.payment_offer:.2f})")
                    msg = "\n".join(lines)

                xml = _build_twilio_response(msg)
                return Response(content=xml, media_type="application/xml")

            # Comando desconhecido no menu principal
            msg = (
                "Opção não reconhecida. No momento, você pode digitar VAGAS "
                "para ver oportunidades próximas."
            )
            xml = _build_twilio_response(msg)
            return Response(content=xml, media_type="application/xml")

        # Fallback para estágios desconhecidos
        user.conversation_stage = "CHOOSING_TYPE"
        db.commit()
        db.refresh(user)

        msg = (
            "Houve um problema ao entender seu estágio de conversa. "
            "Vamos recomeçar. Você busca OPORTUNIDADES ou quer CONTRATAR?"
        )
        xml = _build_twilio_response(msg)
        return Response(content=xml, media_type="application/xml")

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive guard
        print("Erro ao processar webhook do WhatsApp:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a mensagem do WhatsApp.",
        ) from exc

