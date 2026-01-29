import unittest

from app.core.utils import haversine


class TestGeoUtils(unittest.TestCase):
    """
    Testes unitários para funções de geolocalização.

    Comentário (pt-BR):
    Usamos o módulo padrão `unittest` para evitar dependências extras.
    Este teste verifica se a implementação de Haversine está produzindo
    um valor coerente para a distância entre duas cidades reais.
    """

    def test_haversine_sao_jose_jacarei(self) -> None:
        """
        Testa a distância entre São José dos Campos e Jacareí (SP).

        As coordenadas abaixo são aproximações dos centros urbanos.
        A distância real entre as cidades é de aproximadamente 13 km,
        então usamos uma margem de erro razoável para validar o cálculo.
        """

        # Coordenadas aproximadas (graus decimais):
        # São José dos Campos: -23.2237, -45.9009
        # Jacareí:            -23.3053, -45.9658
        sjc_lat, sjc_lon = -23.2237, -45.9009
        jac_lat, jac_lon = -23.3053, -45.9658

        distance_km = haversine(sjc_lat, sjc_lon, jac_lat, jac_lon)

        # Esperamos algo em torno de 13 km, com uma tolerância de 3 km
        self.assertGreater(distance_km, 8.0)
        self.assertLess(distance_km, 18.0)


if __name__ == "__main__":
    unittest.main()

