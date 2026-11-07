from abc import abstractmethod
from typing import List, Optional
from src.domain.entity.product import Product
from src.domain.repository.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """
    Repositório específico para Product com métodos adicionais.
    Segue Clean Architecture mantendo a interface no domínio.
    """

    @abstractmethod
    async def get_by_product_id(self, product_id: int) -> Optional[Product]:
        """Busca produto por product_id"""
        pass

    @abstractmethod
    async def get_by_name(self, product_name: str) -> List[Product]:
        """Busca produtos por nome"""
        pass

    @abstractmethod
    async def get_products_with_logo(self) -> List[Product]:
        """Busca produtos que possuem logo"""
        pass

    @abstractmethod
    async def get_products_with_background(self) -> List[Product]:
        """Busca produtos que possuem background"""
        pass
