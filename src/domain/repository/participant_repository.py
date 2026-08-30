from abc import abstractmethod
from typing import Optional
from src.domain.entity.participant import Participant
from src.domain.repository.base_repository import BaseRepository

class ParticipantRepository(BaseRepository[Participant]):
    """
    Repositório específico para Participant com métodos adicionais.
    Segue Clean Architecture mantendo a interface no domínio.
    """
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Participant]:
        """Busca participante por email"""
        pass

    @abstractmethod
    def email_exists(self, email: str) -> bool:
        """Verifica se um email já existe"""
        pass
