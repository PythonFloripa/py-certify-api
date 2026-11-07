from abc import abstractmethod
from typing import List, Optional
from src.domain.entity.order import Order
from src.domain.repository.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """
    Repositório específico para Order com métodos adicionais.
    Segue Clean Architecture mantendo a interface no domínio.
    """

    @abstractmethod
    def get_by_order_id(self, order_id: int) -> Optional[Order]:
        """Busca pedido por order_id"""
        pass

    @abstractmethod
    def get_by_participant_email(self, email: str) -> List[Order]:
        """Busca pedidos por email do participante"""
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int) -> List[Order]:
        """Busca pedidos por product_id"""
        pass

    @abstractmethod
    def get_orders_by_date_range(self, start_date: str, end_date: str) -> List[Order]:
        """Busca pedidos por intervalo de datas"""
        pass
