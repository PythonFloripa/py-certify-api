"""
Estratégias para busca de certificados.
Implementa o padrão Strategy para eliminar múltiplos if/elif na lógica de busca.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from src.domain.entity.certificate import Certificate
from src.domain.repository.certificate_repository import CertificateRepository
from src.application.dto.fetch_certificate_dto import FetchCertificateRequestDto, FetchCertificateResponseDto


logger = logging.getLogger(__name__)


class FetchCertificateStrategy(ABC):
    """Classe base para estratégias de busca de certificados."""
    
    def __init__(self, certificate_repository: CertificateRepository):
        self.certificate_repository = certificate_repository
    
    @abstractmethod
    def can_handle(self, request: FetchCertificateRequestDto) -> bool:
        """Verifica se a estratégia pode processar a requisição."""
        pass
    
    @abstractmethod
    def fetch_certificates(self, request: FetchCertificateRequestDto) -> List[Certificate]:
        """Busca os certificados de acordo com a estratégia específica."""
        pass
    
    @abstractmethod
    def create_error_response(self, request: FetchCertificateRequestDto) -> FetchCertificateResponseDto:
        """Cria resposta de erro específica para a estratégia."""
        pass
    
    def execute(self, request: FetchCertificateRequestDto) -> List[FetchCertificateResponseDto]:
        """
        Executa a estratégia de busca com lógica comum.
        Template Method pattern para reutilizar lógica comum.
        """
        certificates = self.fetch_certificates(request)
        
        if len(certificates) == 0:
            logger.info(f"No certificates found for request: {request}")
            return [self.create_error_response(request)]
        
        return [FetchCertificateResponseDto(
            id=str(certificate.id),
            order_id=certificate.order_id,
            product_id=certificate.product_id,
            participant_name=f"{certificate.participant_first_name or ''} {certificate.participant_last_name or ''}".strip(),
            participant_email=certificate.participant_email,
            certificate_url=certificate.certificate_url,
            certificate_key=certificate.certificate_key,
            created_at=certificate.generated_date,
            updated_at=certificate.generated_date,  # Assumindo que não temos updated_at separado
            email=certificate.participant_email,
            success=certificate.success
        ) for certificate in certificates]


class FetchByOrderIdStrategy(FetchCertificateStrategy):
    """
    Estratégia para buscar certificados APENAS por order_id.
    
    Condição: APENAS order_id presente, sem email nem product_id.
    Exemplo aceito: ?order_id=123
    Exemplos rejeitados: ?order_id=123&email=user@email.com
    """
    
    def can_handle(self, request: FetchCertificateRequestDto) -> bool:
        # Estratégia mutuamente exclusiva: apenas order_id, sem outros parâmetros
        return (request.order_id is not None and 
                request.email is None and 
                request.product_id is None)
    
    def fetch_certificates(self, request: FetchCertificateRequestDto) -> List[Certificate]:
        logger.info(f"Fetching certificate for order_id: {request.order_id}")
        certificates = self.certificate_repository.get_by_order_id(request.order_id)
        logger.info(f"Found {len(certificates)} certificates for order_id: {request.order_id}")
        return certificates
    
    def create_error_response(self, request: FetchCertificateRequestDto) -> FetchCertificateResponseDto:
        return FetchCertificateResponseDto(
            order_id=request.order_id,
            success=False
        )


class FetchByEmailAndProductIdStrategy(FetchCertificateStrategy):
    """
    Estratégia para buscar certificados por email E product_id simultaneamente.
    
    Condição: email E product_id presentes, independente de order_id.
    Exemplo aceito: ?email=user@email.com&product_id=456
    Esta estratégia tem PRIORIDADE mais alta (mais específica).
    """
    
    def can_handle(self, request: FetchCertificateRequestDto) -> bool:
        # Estratégia específica: requer email E product_id simultaneamente
        return request.email is not None and request.product_id is not None
    
    def fetch_certificates(self, request: FetchCertificateRequestDto) -> List[Certificate]:
        logger.info(f"Fetching certificate for email: {request.email} and product_id: {request.product_id}")
        certificates = self.certificate_repository.get_by_email_and_product_id(request.email, request.product_id)
        logger.info(f"Found {len(certificates)} certificates for email: {request.email} and product_id: {request.product_id}")
        return certificates
    
    def create_error_response(self, request: FetchCertificateRequestDto) -> FetchCertificateResponseDto:
        return FetchCertificateResponseDto(
            email=request.email,
            product_id=request.product_id,
            success=False
        )


class FetchByEmailStrategy(FetchCertificateStrategy):
    """
    Estratégia para buscar certificados APENAS por email.
    
    Condição: APENAS email presente, sem product_id nem order_id.
    Exemplo aceito: ?email=user@email.com
    Exemplos rejeitados: ?email=user@email.com&product_id=456
    """
    
    def can_handle(self, request: FetchCertificateRequestDto) -> bool:
        # Estratégia mutuamente exclusiva: apenas email, sem outros parâmetros
        return request.email is not None and request.product_id is None and request.order_id is None
    
    def fetch_certificates(self, request: FetchCertificateRequestDto) -> List[Certificate]:
        logger.info(f"Fetching certificate for email: {request.email}")
        certificates = self.certificate_repository.get_by_participant_email(request.email)
        logger.info(f"Found {len(certificates)} certificates for email: {request.email}")
        return certificates
    
    def create_error_response(self, request: FetchCertificateRequestDto) -> FetchCertificateResponseDto:
        return FetchCertificateResponseDto(
            email=request.email,
            success=False
        )


class FetchByProductIdStrategy(FetchCertificateStrategy):
    """
    Estratégia para buscar certificados APENAS por product_id.
    
    Condição: APENAS product_id presente, sem email nem order_id.
    Exemplo aceito: ?product_id=456
    Exemplos rejeitados: ?product_id=456&email=user@email.com
    """
    
    def can_handle(self, request: FetchCertificateRequestDto) -> bool:
        # Estratégia mutuamente exclusiva: apenas product_id, sem outros parâmetros
        return request.product_id is not None and request.email is None and request.order_id is None
    
    def fetch_certificates(self, request: FetchCertificateRequestDto) -> List[Certificate]:
        logger.info(f"Fetching certificate for product_id: {request.product_id}")
        certificates = self.certificate_repository.get_by_product_id(request.product_id)
        logger.info(f"Found {len(certificates)} certificates for product_id: {request.product_id}")
        return certificates
    
    def create_error_response(self, request: FetchCertificateRequestDto) -> FetchCertificateResponseDto:
        return FetchCertificateResponseDto(
            product_id=request.product_id,
            success=False
        )
