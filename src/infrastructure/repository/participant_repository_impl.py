import logging
import uuid
from typing import List, Optional, Union

from src.domain.entity.participant import Participant
from src.domain.repository.participant_repository import ParticipantRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.infrastructure.aws.dynamodb_keys import (
    EntityType,
    pk,
    sk,
    gsi1pk_email,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if email is None:
        return None
    return email.strip().lower()


class ParticipantRepositoryImpl(ParticipantRepository):
    def __init__(self, dynamodb_service: DynamoDBService):
        self.dynamodb_service = dynamodb_service

    def create(self, entity: Participant) -> Participant:
        try:
            item = self._prepare_item(entity)
            self.dynamodb_service.put_item(item, "single")
            return entity
        except Exception as e:
            logger.error(f"Erro ao criar participante: {str(e)}")
            raise

    def get_by_id(self, entity_id: str) -> Optional[Participant]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "PK = :pk AND SK = :sk",
                {":pk": pk(EntityType.PARTICIPANT, entity_id), ":sk": sk(EntityType.PARTICIPANT, entity_id)},
            )
            if items:
                return Participant(**items[0])
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
            items = self.dynamodb_service.query_table(
                "single",
                "EntityType = :entity_type",
                {":entity_type": EntityType.PARTICIPANT.value},
            )
            return [Participant(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar todos os participantes: {str(e)}")
            raise

    def update(self, entity_id: str, entity: Participant) -> Optional[Participant]:
        try:
            if not self.exists(entity_id):
                return None

            update_data = self._prepare_item(entity)
            update_data.pop("PK", None)
            update_data.pop("SK", None)

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
                {"PK": pk(EntityType.PARTICIPANT, entity_id), "SK": sk(EntityType.PARTICIPANT, entity_id)},
                update_expression,
                expression_values,
                "single",
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
            self.dynamodb_service.delete_item(
                {"PK": pk(EntityType.PARTICIPANT, entity_id), "SK": sk(EntityType.PARTICIPANT, entity_id)},
                "single"
            )
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
                "single",
                "GSI2PK = :gsi2pk",
                {":gsi2pk": gsi1pk_email(email), ":entity_type": EntityType.PARTICIPANT.value},
                index_name="GSI2",
                filter_expression="EntityType = :entity_type",
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

    def _prepare_item(self, entity: Participant) -> dict:
        item = entity.model_dump()
        participant_id = str(entity.id)
        email = _normalize_email(item.get("email"))

        item["PK"] = pk(EntityType.PARTICIPANT, participant_id)
        item["SK"] = sk(EntityType.PARTICIPANT, participant_id)
        item["EntityType"] = EntityType.PARTICIPANT.value
        item["GSI2PK"] = gsi1pk_email(email) if email else None
        item["GSI2SK"] = f"PARTICIPANT#{participant_id}"
        item["id"] = participant_id
        item["email"] = email
        return {k: v for k, v in item.items() if v is not None}
