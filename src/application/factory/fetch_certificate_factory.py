"""
Factory para criação de estratégias de busca de certificados.
Implementa o padrão Factory para eliminar a lógica de seleção de estratégias.
"""

import logging
from typing import List

from src.domain.exception.certificate_not_found import CertificateNotFound
from src.domain.repository.certificate_repository import CertificateRepository
from src.application.dto.fetch_certificate_dto import FetchCertificateRequestDto
from src.application.strategy.fetch_certificate_strategy import (
    FetchCertificateStrategy,
    FetchByOrderIdStrategy,
    FetchByEmailAndProductIdStrategy,
    FetchByEmailStrategy,
    FetchByProductIdStrategy,
)


logger = logging.getLogger(__name__)


class FetchCertificateStrategyFactory:
    """
    Factory responsável por criar e selecionar a estratégia adequada
    para busca de certificados baseada na requisição.
    """

    def __init__(self, certificate_repository: CertificateRepository):
        self.certificate_repository = certificate_repository
        # Registra todas as estratégias disponíveis para o endpoint unificado
        # ESTRATÉGIAS MUTUAMENTE EXCLUSIVAS - cada uma trata um caso específico:
        #
        # Ordem IMPORTANTE: estratégia mais específica primeiro
        self._strategies: List[FetchCertificateStrategy] = [
            # 1. Mais específica: email + product_id (independente de order_id)
            FetchByEmailAndProductIdStrategy(certificate_repository),
            # 2. Apenas order_id (sem email nem product_id)
            FetchByOrderIdStrategy(certificate_repository),
            # 3. Apenas email (sem product_id nem order_id)
            FetchByEmailStrategy(certificate_repository),
            # 4. Apenas product_id (sem email nem order_id)
            FetchByProductIdStrategy(certificate_repository),
        ]

    def get_strategy(
        self, request: FetchCertificateRequestDto
    ) -> FetchCertificateStrategy:
        """
        Seleciona a estratégia adequada baseada na requisição.

        Args:
            request: Requisição de busca de certificado

        Returns:
            Estratégia adequada para processar a requisição

        Raises:
            CertificateNotFound: Quando nenhuma estratégia pode processar a requisição
        """
        logger.info(f"Selecting strategy for request: {request}")

        # Busca a primeira estratégia que pode processar a requisição
        for strategy in self._strategies:
            if strategy.can_handle(request):
                logger.info(f"Selected strategy: {strategy.__class__.__name__}")
                return strategy

        # Se nenhuma estratégia pode processar, levanta exceção
        logger.error(f"No strategy found for request: {request}")
        raise CertificateNotFound(
            order_id=request.order_id,
            product_id=request.product_id,
            email=request.email,
        )

    def add_strategy(self, strategy: FetchCertificateStrategy) -> None:
        """
        Adiciona uma nova estratégia ao factory.
        Útil para extensibilidade futura.

        Args:
            strategy: Nova estratégia a ser adicionada
        """
        self._strategies.append(strategy)
        logger.info(f"Added new strategy: {strategy.__class__.__name__}")

    def get_available_strategies(self) -> List[str]:
        """
        Retorna lista com nomes das estratégias disponíveis.
        Útil para debugging e monitoramento.

        Returns:
            Lista com nomes das classes de estratégias disponíveis
        """
        return [strategy.__class__.__name__ for strategy in self._strategies]
