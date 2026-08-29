import logging
import uuid
from typing import List, Optional, Union

from src.domain.entity.participant import Participant
from src.domain.repository.participant_repository import ParticipantRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if email is None:
        return None
    return email.strip().lower()


class ParticipantRepositoryImpl(ParticipantRepository):
    def __init__(self, dynamodb_service: DynamoDBService, table_name: str = "participants"):
        self.dynamodb_service = dynamodb_service
        self.table_name = table_name

    def create(self, entity: Participant) -> Participant:
        try:
            item = entity.model_dump()
            item["id"] = str(entity.id)
            item["email"] = _normalize_email(item.get("email"))
            self.dynamodb_service.put_item(item, self.table_name)
            return entity
        except Exception as e:
            logger.error(f"Erro ao criar participante: {str(e)}")
            raise

    def get_by_id(self, entity_id: str) -> Optional[Participant]:
        try:
            item = self.dynamodb_service.get_item({"id": entity_id}, self.table_name)
            if item:
                return Participant(**item)
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar participante por ID {entity_id}: {str(e)}")
            raise

    def find_by_id(self, entity_id: Union[str, uuid.UUID]) -> Optional[Participant]:
        try:
            id_str = str(entity_id) if isinstance(entity_id, uuid.UUID) else entity_id
            return self.get_by_id(id_str)

        except Exception as e:
            logger.error(f"Erro ao buscar participante por ID {entity_id}: {str(e)}")
            raise

    def get_all(self) -> List[Participant]:
        try:
            items = self.dynamodb_service.scan_table(self.table_name)
            return [Participant(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar todos os participantes: {str(e)}")
            raise

    def update(self, entity_id: str, entity: Participant) -> Optional[Participant]:
        try:
            if not self.exists(entity_id):
                return None

            update_data = entity.model_dump()
            update_data["email"] = _normalize_email(update_data.get("email"))
            update_data.pop("id", None)

            update_expression = "SET "
            expression_values = {}
            expression_names = {}

            for key, value in update_data.items():
                if value is not None:
                    update_expression += f"#{key} = :{key}, "
                    expression_values[f":{key}"] = value
                    expression_names[f"#{key}"] = key

            update_expression = update_expression.rstrip(", ")

            response = self.dynamodb_service.update_item(
                {"id": entity_id},
                update_expression,
                expression_values,
                self.table_name,
                expression_attribute_names=expression_names,
            )

            if "Attributes" in response:
                result_dict = self.dynamodb_service._convert_from_dynamodb_format(response["Attributes"])
                return Participant(**result_dict)
            return None

        except Exception as e:
            logger.error(f"Erro ao atualizar participante {entity_id}: {str(e)}")
            raise

    def delete(self, entity_id: str) -> bool:
        try:
            self.dynamodb_service.delete_item({"id": entity_id}, self.table_name)
            return True

        except Exception as e:
            logger.error(f"Erro ao remover participante {entity_id}: {str(e)}")
            return False

    def exists(self, entity_id: str) -> bool:
        try:
            return self.get_by_id(entity_id) is not None

        except Exception as e:
            logger.error(f"Erro ao verificar existência do participante {entity_id}: {str(e)}")
            return False

    def get_by_email(self, email: str) -> Optional[Participant]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "email = :email",
                {":email": _normalize_email(email)},
                index_name="participants_by_email_idx",
            )
            if items:
                return Participant(**items[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar participante por email {email}: {str(e)}")
            raise

    def email_exists(self, email: str) -> bool:
        try:
            participant = self.get_by_email(email)
            return participant is not None

        except Exception as e:
            logger.error(f"Erro ao verificar existência do email {email}: {str(e)}")
            return False
