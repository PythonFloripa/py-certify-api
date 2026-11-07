import logging
import uuid
from typing import List, Optional, Union

from src.domain.entity.certificate import Certificate
from src.domain.repository.certificate_repository import CertificateRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.infrastructure.aws.dynamodb_keys import (
    EntityType,
    pk,
    sk,
    gsi1pk_email,
    gsi1sk_certificate,
    gsi2pk_product,
    gsi2sk_certificate,
    gsi3pk_success,
    gsi3sk_certificate,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if email is None:
        return None
    return email.strip().lower()


def _success_flag(success: Optional[bool]) -> int:
    return 1 if success else 0


class CertificateRepositoryImpl(CertificateRepository):
    def __init__(self, dynamodb_service: DynamoDBService):
        self.dynamodb_service = dynamodb_service

    def create(self, entity: Certificate) -> Certificate:
        try:
            item = self._prepare_item(entity)
            self.dynamodb_service.put_item(item, "single")
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
            items = self.dynamodb_service.scan_table(
                "single",
                filter_expression="EntityType = :entity_type",
                expression_values={":entity_type": EntityType.CERTIFICATE.value},
            )
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
            update_data.pop("PK", None)
            update_data.pop("SK", None)
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
                {"PK": pk(EntityType.CERTIFICATE, existing_certificate.order_id),
                 "SK": sk(EntityType.CERTIFICATE, existing_certificate.order_id)},
                update_expression,
                expression_values,
                "single",
                expression_attribute_names=expression_names,
            )

            if "Attributes" in response:
                result_dict = self.dynamodb_service._convert_from_dynamodb_format(response["Attributes"])
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
                {"PK": pk(EntityType.CERTIFICATE, certificate.order_id),
                 "SK": sk(EntityType.CERTIFICATE, certificate.order_id)},
                "single"
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
            logger.error(f"Erro ao verificar existência do certificado {entity_id}: {str(e)}")
            return False

    def find_by_id(self, entity_id: Union[str, uuid.UUID]) -> Optional[Certificate]:
        try:
            normalized_id = str(entity_id)
            items = self.dynamodb_service.query_table(
                "single",
                "GSI1PK = :gsi1pk",
                {":gsi1pk": f"CERT#{normalized_id}"},
                index_name="GSI1",
            )
            if items:
                return Certificate(**items[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar certificado por UUID {entity_id}: {str(e)}")
            raise

    def get_by_order_id(self, order_id: int) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "PK = :pk AND SK = :sk",
                {":pk": pk(EntityType.CERTIFICATE, order_id),
                 ":sk": sk(EntityType.CERTIFICATE, order_id)},
            )
            if not items:
                return []
            return [Certificate(**items[0])]
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por order_id {order_id}: {str(e)}")
            raise

    def get_by_participant_email(self, email: str) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "GSI2PK = :gsi2pk AND begins_with(GSI2SK, :sk_prefix)",
                {":gsi2pk": gsi1pk_email(email), ":sk_prefix": "CERTIFICATE#", ":entity_type": EntityType.CERTIFICATE.value},
                index_name="GSI2",
                scan_index_forward=False,
                filter_expression="EntityType = :entity_type",
            )
            return [Certificate(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por email {email}: {str(e)}")
            raise

    def get_by_email_and_product_id(self, email: str, product_id: int) -> List[Certificate]:
        try:
            normalized_email = _normalize_email(email)
            items = self.dynamodb_service.query_table(
                "single",
                "GSI2PK = :gsi2pk AND begins_with(GSI2SK, :sk_prefix)",
                {":gsi2pk": gsi1pk_email(normalized_email), ":sk_prefix": "CERTIFICATE#", ":entity_type": EntityType.CERTIFICATE.value},
                index_name="GSI2",
                scan_index_forward=False,
                filter_expression="EntityType = :entity_type",
            )
            certificates = [Certificate(**item) for item in items if item.get("product_id") == product_id]
            logger.info(
                "Encontrados %s certificados para email %s e product_id %s",
                len(certificates),
                email,
                product_id,
            )
            return certificates
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por email {email} e product_id {product_id}: {str(e)}")
            raise

    def get_by_product_id(self, product_id: int) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "GSI3PK = :gsi3pk AND begins_with(GSI3SK, :sk_prefix)",
                {":gsi3pk": gsi2pk_product(product_id), ":sk_prefix": "CERTIFICATE#"},
                index_name="GSI3",
                scan_index_forward=False,
            )
            return [Certificate(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por product_id {product_id}: {str(e)}")
            raise

    def get_successful_certificates(self) -> List[Certificate]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "GSI4PK = :gsi4pk AND begins_with(GSI4SK, :sk_prefix)",
                {":gsi4pk": gsi3pk_success(True), ":sk_prefix": "CERTIFICATE#"},
                index_name="GSI4",
                scan_index_forward=False,
            )
            return [Certificate(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar certificados bem-sucedidos: {str(e)}")
            raise

    def _prepare_item(self, entity: Certificate) -> dict:
        item = entity.model_dump()
        cert_id = str(entity.id)
        order_id = entity.order_id
        email = _normalize_email(item.get("participant_email"))
        success = item.get("success", False)

        item["PK"] = pk(EntityType.CERTIFICATE, order_id)
        item["SK"] = sk(EntityType.CERTIFICATE, order_id)
        item["EntityType"] = EntityType.CERTIFICATE.value
        item["GSI1PK"] = f"CERT#{cert_id}"
        item["GSI1SK"] = f"CERTIFICATE#{order_id}"
        item["GSI2PK"] = gsi1pk_email(email) if email else None
        item["GSI2SK"] = f"CERTIFICATE#{order_id}"
        item["GSI3PK"] = gsi2pk_product(entity.product_id)
        item["GSI3SK"] = gsi2sk_certificate(order_id)
        item["GSI4PK"] = gsi3pk_success(success)
        item["GSI4SK"] = gsi3sk_certificate(order_id)
        item["id"] = cert_id
        item["participant_email"] = email
        item["success_flag"] = _success_flag(success)
        return {k: v for k, v in item.items() if v is not None}
