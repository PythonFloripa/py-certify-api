import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Union

from src.domain.entity.order import Order
from src.domain.repository.order_repository import OrderRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.infrastructure.aws.dynamodb_keys import (
    EntityType,
    pk,
    sk,
    gsi1pk_email,
    gsi2pk_product,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _parse_order_date(value: str) -> datetime:
    normalized_value = value.replace("Z", "+00:00")
    for parser in (
        lambda: datetime.fromisoformat(normalized_value),
        lambda: datetime.strptime(value, "%Y-%m-%d %H:%M:%S"),
        lambda: datetime.strptime(value, "%Y-%m-%d"),
    ):
        try:
            return parser()
        except ValueError:
            continue
    raise ValueError(f"Formato de order_date não suportado: {value}")


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def _order_year_month(value: str) -> str:
    return _parse_order_date(value).strftime("%Y-%m")


def _order_date_order_id(value: str, order_id: int) -> str:
    return f"{_parse_order_date(value).isoformat()}#{order_id:020d}"


class OrderRepositoryImpl(OrderRepository):
    def __init__(self, dynamodb_service: DynamoDBService):
        self.dynamodb_service = dynamodb_service

    def create(self, entity: Order) -> Order:
        try:
            item = self._prepare_item(entity)
            self.dynamodb_service.put_item(item, "single")
            return entity
        except Exception as e:
            logger.error(f"Erro ao criar pedido: {str(e)}")
            raise

    def get_by_id(self, entity_id: int) -> Optional[Order]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "PK = :pk AND SK = :sk",
                {":pk": pk(EntityType.ORDER, entity_id), ":sk": sk(EntityType.ORDER, entity_id)},
            )
            if items:
                return Order(**items[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar pedido por ID {entity_id}: {str(e)}")
            raise

    def find_by_id(self, entity_id: Union[str, uuid.UUID]) -> Optional[Order]:
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
            logger.error(f"Erro ao buscar pedido por ID {entity_id}: {str(e)}")
            raise

    def get_all(self) -> List[Order]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "EntityType = :entity_type",
                {":entity_type": EntityType.ORDER.value},
            )
            return [Order(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar todos os pedidos: {str(e)}")
            raise

    def update(self, entity_id: int, entity: Order) -> Optional[Order]:
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
                {"PK": pk(EntityType.ORDER, entity_id), "SK": sk(EntityType.ORDER, entity_id)},
                update_expression,
                expression_values,
                "single",
                expression_attribute_names=expression_names,
            )

            if "Attributes" in response:
                result_dict = self.dynamodb_service._convert_from_dynamodb_format(response["Attributes"])
                return Order(**result_dict)
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar pedido {entity_id}: {str(e)}")
            raise

    def delete(self, entity_id: int) -> bool:
        try:
            self.dynamodb_service.delete_item(
                {"PK": pk(EntityType.ORDER, entity_id), "SK": sk(EntityType.ORDER, entity_id)},
                "single"
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao remover pedido {entity_id}: {str(e)}")
            return False

    def exists(self, entity_id: int) -> bool:
        try:
            return self.get_by_id(entity_id) is not None
        except Exception as e:
            logger.error(f"Erro ao verificar existência do pedido {entity_id}: {str(e)}")
            return False

    def get_by_order_id(self, order_id: int) -> Optional[Order]:
        return self.get_by_id(order_id)

    def get_by_participant_email(self, email: str) -> List[Order]:
        try:
            normalized_email = _normalize_email(email)
            items = self.dynamodb_service.query_table(
                "single",
                "GSI2PK = :gsi2pk AND begins_with(GSI2SK, :sk_prefix)",
                {":gsi2pk": gsi1pk_email(normalized_email), ":sk_prefix": "ORDER#", ":entity_type": EntityType.ORDER.value},
                index_name="GSI2",
                scan_index_forward=False,
                filter_expression="EntityType = :entity_type",
            )
            return [Order(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar pedidos por email {email}: {str(e)}")
            raise

    def get_by_product_id(self, product_id: int) -> List[Order]:
        try:
            items = self.dynamodb_service.query_table(
                "single",
                "GSI3PK = :gsi3pk AND begins_with(GSI3SK, :sk_prefix)",
                {":gsi3pk": gsi2pk_product(product_id), ":sk_prefix": "ORDER#"},
                index_name="GSI3",
                scan_index_forward=False,
            )
            return [Order(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar pedidos por product_id {product_id}: {str(e)}")
            raise

    def get_orders_by_date_range(self, start_date: str, end_date: str) -> List[Order]:
        try:
            start_dt = _as_naive_utc(_parse_order_date(start_date))
            end_dt = _as_naive_utc(_parse_order_date(end_date))
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt

            current_month = datetime(start_dt.year, start_dt.month, 1)
            final_month = datetime(end_dt.year, end_dt.month, 1)
            items = []

            while current_month <= final_month:
                month_key = current_month.strftime("%Y-%m")
                month_start = max(start_dt, current_month)
                next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
                month_end_boundary = next_month - timedelta(microseconds=1)
                month_end = min(end_dt, month_end_boundary)

                month_items = self.dynamodb_service.query_table(
                    "single",
                    "order_year_month = :order_year_month AND order_date_order_id BETWEEN :start_range AND :end_range",
                    {
                        ":order_year_month": month_key,
                        ":start_range": f"{month_start.isoformat()}#00000000000000000000",
                        ":end_range": f"{month_end.isoformat()}#99999999999999999999",
                    },
                )
                items.extend(month_items)
                current_month = next_month

            return [Order(**item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao buscar pedidos por intervalo de datas {start_date} - {end_date}: {str(e)}")
            raise

    def _prepare_item(self, entity: Order) -> dict:
        item = entity.model_dump()
        order_id = item["order_id"]
        email = _normalize_email(item["participant_email"])

        item["PK"] = pk(EntityType.ORDER, order_id)
        item["SK"] = sk(EntityType.ORDER, order_id)
        item["EntityType"] = EntityType.ORDER.value
        item["GSI2PK"] = gsi1pk_email(email)
        item["GSI2SK"] = f"ORDER#{order_id}"
        item["GSI3PK"] = gsi2pk_product(item["product_id"])
        item["GSI3SK"] = f"ORDER#{order_id}"
        item["participant_email"] = email
        item["order_year_month"] = _order_year_month(item["order_date"])
        item["order_date_order_id"] = _order_date_order_id(item["order_date"], order_id)
        return item
