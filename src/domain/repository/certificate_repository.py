from abc import abstractmethod
from typing import List
from src.domain.entity.certificate import Certificate
from src.domain.repository.base_repository import BaseRepository


class CertificateRepository(BaseRepository[Certificate]):
    """
    Repositório específico para Certificate com métodos adicionais.
    Segue Clean Architecture mantendo a interface no domínio.
    """

    @abstractmethod
    def get_by_order_id(self, order_id: int) -> List[Certificate]:
        """Busca certificados por order_id"""
        pass

    @abstractmethod
    def get_by_participant_email(self, email: str) -> List[Certificate]:
        """Busca certificados por email do participante"""
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> List[Certificate]:
        """Busca certificados por product_id"""
        pass

    @abstractmethod
    def get_by_email_and_product_id(
        self, email: str, product_id: int
    ) -> List[Certificate]:
        """Busca certificados por email do participante e product_id"""
        pass

    @abstractmethod
    def get_successful_certificates(self) -> List[Certificate]:
        """Busca apenas certificados com sucesso=True"""
        pass
