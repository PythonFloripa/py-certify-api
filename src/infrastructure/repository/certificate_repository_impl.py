import logging
import uuid
from typing import List, Optional, Union

from src.domain.entity.certificate import Certificate
from src.domain.repository.certificate_repository import CertificateRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if email is None:
        return None
    return email.strip().lower()


def _email_product_key(
    email: Optional[str], product_id: Optional[int]
) -> Optional[str]:
    normalized_email = _normalize_email(email)
    if not normalized_email or product_id is None:
        return None
    return f"{normalized_email}#{product_id}"


def _success_flag(success: Optional[bool]) -> int:
    return 1 if success else 0


class CertificateRepositoryImpl(CertificateRepository):
    def __init__(
        self, dynamodb_service: DynamoDBService, table_name: str = "certificates"
    ):
        self.dynamodb_service = dynamodb_service
        self.table_name = table_name

    def create(self, entity: Certificate) -> Certificate:
        try:
            item = self._prepare_item(entity)
            self.dynamodb_service.put_item(item, self.table_name)

            logger.info(f"Certificado criado com sucesso: {entity.id}")
            return entity

        except Exception as e:
            logger.error(f"Erro ao criar certificado: {str(e)}")
            raise

    def get_by_id(self, entity_id: str, order_id: int = None) -> Optional[Certificate]:
        try:
            certificate = self.find_by_id(entity_id)
            if not certificate:
                return None

            if order_id is not None and certificate.order_id != order_id:
                return None

            return certificate

        except Exception as e:
            logger.error(f"Erro ao buscar certificado por ID {entity_id}: {str(e)}")
            raise

    def get_all(self) -> List[Certificate]:
        try:
            items = self.dynamodb_service.scan_table(self.table_name)
            return [Certificate(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar todos os certificados: {str(e)}")
            raise

    def update(self, entity_id: str, entity: Certificate) -> Optional[Certificate]:
        try:
            existing_certificate = self.find_by_id(entity_id)
            if not existing_certificate:
                return None

            update_data = self._prepare_item(entity)
            update_data.pop("id", None)
            update_data.pop("order_id", None)

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
                {"order_id": existing_certificate.order_id},
                update_expression,
                expression_values,
                self.table_name,
                expression_attribute_names=expression_names,
            )

            if "Attributes" in response:
                result_dict = self.dynamodb_service._convert_from_dynamodb_format(
                    response["Attributes"]
                )
                return Certificate(**result_dict)
            return None

        except Exception as e:
            logger.error(f"Erro ao atualizar certificado {entity_id}: {str(e)}")
            raise

    def delete(self, entity_id: str, order_id: int = None) -> bool:
        try:
            certificate = self.get_by_id(entity_id, order_id)
            if not certificate:
                return False

            self.dynamodb_service.delete_item(
                {"order_id": certificate.order_id}, self.table_name
            )
            logger.info(f"Certificado {entity_id} removido com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao remover certificado {entity_id}: {str(e)}")
            return False

    def exists(self, entity_id: str, order_id: int = None) -> bool:
        try:
            return self.get_by_id(entity_id, order_id) is not None

        except Exception as e:
            logger.error(
                f"Erro ao verificar existência do certificado {entity_id}: {str(e)}"
            )
            return False

    def find_by_id(self, entity_id: Union[str, uuid.UUID]) -> Optional[Certificate]:
        try:
            normalized_id = str(entity_id)
            items = self.dynamodb_service.query_table(
                self.table_name,
                "id = :id",
                {":id": normalized_id},
                index_name="certificate_id_idx",
            )
            if items:
                return Certificate(**items[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar certificado por UUID {entity_id}: {str(e)}")
            raise

    def get_by_order_id(self, order_id: int) -> List[Certificate]:
        try:
            item = self.dynamodb_service.get_item(
                {"order_id": order_id}, self.table_name
            )
            if not item:
                return []
            return [Certificate(**item)]

        except Exception as e:
            logger.error(
                f"Erro ao buscar certificados por order_id {order_id}: {str(e)}"
            )
            raise

    def get_by_participant_email(self, email: str) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "participant_email = :email",
                {":email": _normalize_email(email)},
                index_name="certificates_by_email_idx",
                scan_index_forward=False,
            )
            return [Certificate(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar certificados por email {email}: {str(e)}")
            raise

    def get_by_email_and_product_id(
        self, email: str, product_id: int
    ) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "participant_email_product_key = :email_product_key",
                {":email_product_key": _email_product_key(email, product_id)},
                index_name="certificates_by_email_product_idx",
                scan_index_forward=False,
            )
            certificates = [Certificate(**item) for item in items]
            logger.info(
                "Encontrados %s certificados para email %s e product_id %s",
                len(certificates),
                email,
                product_id,
            )
            return certificates

        except Exception as e:
            logger.error(
                f"Erro ao buscar certificados por email {email} e product_id {product_id}: {str(e)}"
            )
            raise

    def get_by_product_id(self, product_id: int) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "product_id = :product_id",
                {":product_id": product_id},
                index_name="certificates_by_product_idx",
                scan_index_forward=False,
            )
            return [Certificate(**item) for item in items]

        except Exception as e:
            logger.error(
                f"Erro ao buscar certificados por product_id {product_id}: {str(e)}"
            )
            raise

    def get_successful_certificates(self) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "success_flag = :success_flag",
                {":success_flag": 1},
                index_name="certificates_by_success_idx",
                scan_index_forward=False,
            )
            return [Certificate(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar certificados bem-sucedidos: {str(e)}")
            raise

    def _prepare_item(self, entity: Certificate) -> dict:
        item = entity.model_dump()
        item["id"] = str(entity.id)
        item["participant_email"] = _normalize_email(item.get("participant_email"))
        item["participant_email_product_key"] = _email_product_key(
            item.get("participant_email"),
            item.get("product_id"),
        )
        item["success_flag"] = _success_flag(item.get("success"))
        return item
