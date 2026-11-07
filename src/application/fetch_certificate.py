import logging
from typing import List

from src.domain.repository.certificate_repository import CertificateRepository
from src.infrastructure.container.dependency_container import container
from src.application.dto.fetch_certificate_dto import (
    FetchCertificateRequestDto,
    FetchCertificateResponseDto,
)
from src.application.factory.fetch_certificate_factory import (
    FetchCertificateStrategyFactory,
)


logger = logging.getLogger(__name__)


class FetchCertificate:
    def __init__(self):
        self.certificate_repository: CertificateRepository = container.get(
            "certificate_repository"
        )
        self.strategy_factory = FetchCertificateStrategyFactory(
            self.certificate_repository
        )

    def execute(
        self, request: FetchCertificateRequestDto
    ) -> List[FetchCertificateResponseDto]:
        """
        Executa a busca de certificados usando a estratégia adequada.

        Args:
            request: Requisição com os parâmetros de busca

        Returns:
            Lista de respostas com os certificados encontrados ou erro

        Raises:
            CertificateNotFound: Quando nenhuma estratégia pode processar a requisição
        """
        logger.info(f"Fetching certificate for request: {request}")

        # Factory seleciona automaticamente a estratégia correta
        strategy = self.strategy_factory.get_strategy(request)

        # Estratégia executa a lógica específica de busca
        return strategy.execute(request)
