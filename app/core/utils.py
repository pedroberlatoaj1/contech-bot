import math
from collections.abc import Iterable
from typing import List

from app.models.models import JobOpportunity


# Comentário (pt-BR):
# Este módulo concentra utilitários de geolocalização, incluindo:
# - Cálculo de distância entre dois pontos (Haversine)
# - Filtro de oportunidades de trabalho próximas a um usuário


EARTH_RADIUS_KM: float = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance between two points on Earth (in kilometers).

    The formula used is the Haversine formula, which assume the Earth as a sphere
    and is precise enough for distâncias em escala de cidades/países.

    Args:
        lat1: Latitude do primeiro ponto (em graus decimais).
        lon1: Longitude do primeiro ponto (em graus decimais).
        lat2: Latitude do segundo ponto (em graus decimais).
        lon2: Longitude do segundo ponto (em graus decimais).

    Returns:
        Distância em quilômetros entre os dois pontos.

    Comentário (pt-BR):
    A matemática funciona assim:
    - Convertemos graus para radianos
    - Aplicamos a fórmula de Haversine para o ângulo central
    - Multiplicamos pelo raio da Terra para obter a distância linear
    """

    # Converte graus para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferenças
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Fórmula de Haversine
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    distance_km = EARTH_RADIUS_KM * c
    return distance_km


def find_nearby_jobs(
    user_lat: float,
    user_lon: float,
    jobs: Iterable[JobOpportunity],
    radius_km: float = 10.0,
) -> list[JobOpportunity]:
    """
    Filter job opportunities that are within a given radius (in kilometers).

    Args:
        user_lat: Latitude do usuário.
        user_lon: Longitude do usuário.
        jobs: Iterable de objetos JobOpportunity (normalmente vindos do banco).
        radius_km: Raio máximo de busca, em quilômetros.

    Returns:
        Lista de JobOpportunity que estão dentro do raio especificado.

    Comentário (pt-BR):
    Esta função não faz acesso ao banco diretamente; ela apenas recebe
    as oportunidades (por exemplo, já carregadas via SQLAlchemy) e aplica
    o filtro em memória. Isso facilita o teste unitário e a reutilização.
    """

    nearby: list[JobOpportunity] = []

    for job in jobs:
        # Por segurança, ignoramos registros sem coordenadas válidas.
        if job.latitude is None or job.longitude is None:
            continue

        distance = haversine(user_lat, user_lon, job.latitude, job.longitude)

        if distance <= radius_km:
            nearby.append(job)

    return nearby

