from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Union
from pydantic import BaseModel
import uuid

# Tipo genérico para as entidades
T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """
    Repositório base abstrato seguindo Clean Architecture.
    Define a interface para operações CRUD básicas.
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Cria uma nova entidade no repositório"""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Busca uma entidade pelo ID"""
        pass

    @abstractmethod
    def find_by_id(self, entity_id: Union[str, uuid.UUID]) -> Optional[T]:
        """Busca uma entidade pelo UUID"""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Busca todas as entidades"""
        pass

    @abstractmethod
    def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Atualiza uma entidade existente"""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Remove uma entidade pelo ID"""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Verifica se uma entidade existe"""
        pass
