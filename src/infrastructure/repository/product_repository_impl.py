import logging
import uuid
from typing import List, Optional, Union

from src.domain.entity.product import Product
from src.domain.repository.product_repository import ProductRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _flag(value: Optional[str]) -> int:
    return 1 if value else 0


class ProductRepositoryImpl(ProductRepository):
    def __init__(self, dynamodb_service: DynamoDBService, table_name: str = "products"):
        self.dynamodb_service = dynamodb_service
        self.table_name = table_name

    def create(self, entity: Product) -> Product:
        try:
            item = self._prepare_item(entity)
            self.dynamodb_service.put_item(item, self.table_name)
            return entity

        except Exception as e:
            logger.error(f"Erro ao criar produto: {str(e)}")
            raise

    def get_by_id(self, entity_id: int) -> Optional[Product]:
        try:
            item = self.dynamodb_service.get_item(
                {"product_id": entity_id}, self.table_name
            )
            if item:
                return Product(**item)
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar produto por ID {entity_id}: {str(e)}")
            raise

    def find_by_id(self, entity_id: Union[str, uuid.UUID]) -> Optional[Product]:
        try:
            if isinstance(entity_id, uuid.UUID):
                id_str = str(entity_id)
                id_int = int(id_str.replace("-", "")[:10])
            else:
                id_int = int(str(entity_id))

            return self.get_by_id(id_int)

        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao converter ID {entity_id} para int: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar produto por ID {entity_id}: {str(e)}")
            raise

    def get_all(self) -> List[Product]:
        try:
            items = self.dynamodb_service.scan_table(self.table_name)
            return [Product(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar todos os produtos: {str(e)}")
            raise

    def update(self, entity_id: int, entity: Product) -> Optional[Product]:
        try:
            if not self.exists(entity_id):
                return None

            update_data = self._prepare_item(entity)
            update_data.pop("product_id", None)

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
                {"product_id": entity_id},
                update_expression,
                expression_values,
                self.table_name,
                expression_attribute_names=expression_names,
            )

            if "Attributes" in response:
                result_dict = self.dynamodb_service._convert_from_dynamodb_format(
                    response["Attributes"]
                )
                return Product(**result_dict)
            return None

        except Exception as e:
            logger.error(f"Erro ao atualizar produto {entity_id}: {str(e)}")
            raise

    def delete(self, entity_id: int) -> bool:
        try:
            self.dynamodb_service.delete_item(
                {"product_id": entity_id}, self.table_name
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao remover produto {entity_id}: {str(e)}")
            return False

    def exists(self, entity_id: int) -> bool:
        try:
            return self.get_by_id(entity_id) is not None

        except Exception as e:
            logger.error(
                f"Erro ao verificar existência do produto {entity_id}: {str(e)}"
            )
            return False

    def get_by_product_id(self, product_id: int) -> Optional[Product]:
        try:
            return self.get_by_id(product_id)

        except Exception as e:
            logger.error(
                f"Erro ao buscar produto por product_id {product_id}: {str(e)}"
            )
            raise

    def get_by_name(self, product_name: str) -> List[Product]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "product_name = :product_name",
                {":product_name": product_name},
                index_name="products_by_name_idx",
            )
            return [Product(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar produtos por nome {product_name}: {str(e)}")
            raise

    def get_products_with_logo(self) -> List[Product]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "has_certificate_logo_flag = :flag",
                {":flag": 1},
                index_name="products_by_has_logo_idx",
            )
            return [Product(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar produtos com logo: {str(e)}")
            raise

    def get_products_with_background(self) -> List[Product]:
        try:
            items = self.dynamodb_service.query_table(
                self.table_name,
                "has_certificate_background_flag = :flag",
                {":flag": 1},
                index_name="products_by_has_background_idx",
            )
            return [Product(**item) for item in items]

        except Exception as e:
            logger.error(f"Erro ao buscar produtos com background: {str(e)}")
            raise

    def _prepare_item(self, entity: Product) -> dict:
        item = entity.model_dump()
        item["has_certificate_logo_flag"] = _flag(item.get("certificate_logo"))
        item["has_certificate_background_flag"] = _flag(
            item.get("certificate_background")
        )
        return item
