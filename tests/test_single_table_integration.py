"""
Teste de integração end-to-end com MiniStack.
Este teste valida o design single-table com operações CRUD reais.
"""

import os
import sys
import uuid

os.environ.setdefault("REGION", "us-west-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import boto3
from src.domain.entity.order import Order
from src.domain.entity.certificate import Certificate
from src.domain.entity.product import Product
from src.domain.entity.participant import Participant


class DynamoDBServiceMiniStack:
    def __init__(self):
        import os
        endpoint_url = os.environ.get("ENDPOINT_URL", "http://localhost:4566")
        self.aws = boto3.client(
            'dynamodb',
            region_name=os.environ.get("REGION", "us-west-2"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
            endpoint_url=endpoint_url
        )
        self.table_name = "tech-floripa-certificates-dev"

    def put_item(self, item: dict, table_name: str = None) -> dict:
        item = self._convert_to_dynamodb_format(item)
        return self.aws.put_item(
            TableName=self.table_name,
            Item=item
        )

    def get_item(self, key: dict, table_name: str = None) -> dict:
        key = self._convert_to_dynamodb_format(key)
        response = self.aws.get_item(
            TableName=self.table_name,
            Key=key
        )
        if 'Item' in response:
            return self._convert_from_dynamodb_format(response['Item'])
        return None

    def query_table(self, table_name: str, key_condition_expression: str, expression_values: dict,
                    index_name: str = None, scan_index_forward: bool = True, filter_expression: str = None) -> list:
        expression_values = self._convert_to_dynamodb_format(expression_values)
        kwargs = {
            "TableName": self.table_name,
            "KeyConditionExpression": key_condition_expression,
            "ExpressionAttributeValues": expression_values,
            "ScanIndexForward": scan_index_forward,
        }
        if index_name:
            kwargs['IndexName'] = index_name
        if filter_expression:
            kwargs['FilterExpression'] = filter_expression

        items = []
        while True:
            response = self.aws.query(**kwargs)
            if 'Items' in response:
                for item in response['Items']:
                    items.append(self._convert_from_dynamodb_format(item))
            if 'LastEvaluatedKey' not in response:
                break
            kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        return items

    def scan_table(self, table_name: str, filter_expression: str = None, expression_values: dict = None) -> list:
        kwargs = {"TableName": self.table_name}
        if filter_expression and expression_values:
            kwargs['FilterExpression'] = filter_expression
            kwargs['ExpressionAttributeValues'] = self._convert_to_dynamodb_format(expression_values)
        items = []
        while True:
            response = self.aws.scan(**kwargs)
            if 'Items' in response:
                for item in response['Items']:
                    items.append(self._convert_from_dynamodb_format(item))
            if 'LastEvaluatedKey' not in response:
                break
            kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        return items

    def update_item(self, key: dict, update_expression: str, expression_values: dict,
                    table_name: str, expression_attribute_names: dict = None) -> dict:
        key = self._convert_to_dynamodb_format(key)
        expression_values = self._convert_to_dynamodb_format(expression_values)
        kwargs = {
            "TableName": self.table_name,
            "Key": key,
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }
        if expression_attribute_names:
            kwargs["ExpressionAttributeNames"] = expression_attribute_names
        return self.aws.update_item(**kwargs)

    def delete_item(self, key: dict, table_name: str = None) -> dict:
        key = self._convert_to_dynamodb_format(key)
        return self.aws.delete_item(
            TableName=self.table_name,
            Key=key
        )

    def _convert_to_dynamodb_format(self, data):
        if isinstance(data, dict):
            return {k: self._convert_to_dynamodb_format(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_dynamodb_format(item) for item in data]
        elif isinstance(data, str):
            return {'S': data}
        elif isinstance(data, uuid.UUID):
            return {'S': str(data)}
        elif isinstance(data, bool):
            return {'BOOL': data}
        elif isinstance(data, int):
            return {'N': str(data)}
        elif isinstance(data, float):
            return {'N': str(data)}
        elif data is None:
            return {'NULL': True}
        else:
            return {'S': str(data)}

    def _convert_from_dynamodb_format(self, data):
        if isinstance(data, dict):
            if len(data) == 1:
                key = list(data.keys())[0]
                if key == 'S':
                    return data['S']
                elif key == 'N':
                    return float(data['N'])
                elif key == 'BOOL':
                    return data['BOOL']
                elif key == 'L':
                    return [self._convert_from_dynamodb_format(item) for item in data['L']]
                elif key == 'M':
                    return {k: self._convert_from_dynamodb_format(v) for k, v in data['M'].items()}
                elif key == 'NULL':
                    return None
            return {k: self._convert_from_dynamodb_format(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_from_dynamodb_format(item) for item in data]
        else:
            return data


from src.infrastructure.repository.order_repository_impl import OrderRepositoryImpl
from src.infrastructure.repository.certificate_repository_impl import CertificateRepositoryImpl
from src.infrastructure.repository.product_repository_impl import ProductRepositoryImpl
from src.infrastructure.repository.participant_repository_impl import ParticipantRepositoryImpl


def test_single_table_crud():
    print("\n=== Testando Single-Table Design com MiniStack ===\n")

    dynamodb_service = DynamoDBServiceMiniStack()

    order_repo = OrderRepositoryImpl(dynamodb_service)
    cert_repo = CertificateRepositoryImpl(dynamodb_service)
    product_repo = ProductRepositoryImpl(dynamodb_service)
    participant_repo = ParticipantRepositoryImpl(dynamodb_service)

    print("1. Criando Product...")
    product = Product(
        product_id=316,
        product_name="Python Workshop",
        certificate_details="Workshop de Python",
        certificate_logo="logo.png",
        certificate_background="bg.png",
        checkin_latitude="-27.59",
        checkin_longitude="-48.55",
        time_checkin="09:00"
    )
    created_product = product_repo.create(product)
    print(f"   Product criado: {created_product.product_id}")

    print("\n2. Criando Participant...")
    participant = Participant(
        id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+5511999999999",
        cpf="12345678900",
        city="Florianopolis"
    )
    created_participant = participant_repo.create(participant)
    print(f"   Participant criado: {created_participant.email}")

    print("\n3. Criando Order...")
    order = Order(
        order_id=1001,
        order_date="2025-01-15 10:00:00",
        product_id=316,
        product_name="Python Workshop",
        certificate_details="Workshop de Python",
        certificate_logo="logo.png",
        certificate_background="bg.png",
        checkin_latitude="-27.59",
        checkin_longitude="-48.55",
        time_checkin="09:00",
        participant_email="john.doe@example.com",
        participant_first_name="John",
        participant_last_name="Doe",
        participant_cpf="12345678900",
        participant_phone="+5511999999999",
        participant_city="Florianopolis"
    )
    created_order = order_repo.create(order)
    print(f"   Order criada: {created_order.order_id}")

    print("\n4. Criando Certificate...")
    cert_id = uuid.uuid4()
    certificate = Certificate(
        id=cert_id,
        success=False,
        certificate_key=None,
        certificate_url=None,
        generated_date=None,
        order_id=1001,
        order_date="2025-01-15 10:00:00",
        product_id=316,
        product_name="Python Workshop",
        certificate_details="Workshop de Python",
        certificate_logo="logo.png",
        certificate_background="bg.png",
        participant_email="john.doe@example.com",
        participant_first_name="John",
        participant_last_name="Doe",
        participant_cpf="12345678900",
        participant_phone="+5511999999999",
        participant_city="Florianopolis"
    )
    created_cert = cert_repo.create(certificate)
    print(f"   Certificate criado: {created_cert.id}")

    print("\n5. Buscando por ID...")
    found_order = order_repo.get_by_id(1001)
    print(f"   Order encontrada: {found_order.order_id if found_order else 'NONE'}")

    print("\n6. Buscando Product por ID...")
    found_product = product_repo.get_by_id(316)
    print(f"   Product encontrada: {found_product.product_name if found_product else 'NONE'}")

    print("\n7. Buscando Participant por email...")
    found_participant = participant_repo.get_by_email("john.doe@example.com")
    print(f"   Participant encontrado: {found_participant.email if found_participant else 'NONE'}")

    print("\n8. Buscando Certificate por order_id...")
    found_certs = cert_repo.get_by_order_id(1001)
    print(f"   Certificates encontrados: {len(found_certs)}")

    print("\n9. Buscando Orders por email...")
    orders_by_email = order_repo.get_by_participant_email("john.doe@example.com")
    print(f"   Orders por email: {len(orders_by_email)}")

    print("\n10. Buscando Certificates por email...")
    certs_by_email = cert_repo.get_by_participant_email("john.doe@example.com")
    print(f"   Certificates por email: {len(certs_by_email)}")

    print("\n11. Buscando Certificates por product_id...")
    certs_by_product = cert_repo.get_by_product_id(316)
    print(f"   Certificates por product_id: {len(certs_by_product)}")

    print("\n12. Atualizando Certificate (simulando sucesso)...")
    certificate.success = True
    certificate.certificate_key = "cert-1001-key"
    updated_cert = cert_repo.update(str(cert_id), certificate)
    print(f"   Certificate atualizado: success={updated_cert.success if updated_cert else 'NONE'}")

    print("\n13. Buscando Certificates bem-sucedidos...")
    successful_certs = cert_repo.get_successful_certificates()
    print(f"   Certificates bem-sucedidos: {len(successful_certs)}")

    print("\n14. Deletando Certificate...")
    deleted = cert_repo.delete(str(cert_id))
    print(f"   Certificate deletado: {deleted}")

    print("\n15. Listando todos os Certificates...")
    all_certs = cert_repo.get_all()
    print(f"   Total de certificates: {len(all_certs)}")

    print("\n16. Listando todos os Products...")
    all_products = product_repo.get_all()
    print(f"   Total de products: {len(all_products)}")

    print("\n=== Teste Concluído com Sucesso! ===\n")

    return True


if __name__ == "__main__":
    try:
        test_single_table_crud()
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
