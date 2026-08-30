import os
import sys
import types
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("REGION", "us-east-1")
os.environ.setdefault("BUILDER_QUEUE_URL", "https://example.com/queue")
os.environ.setdefault("S3_BUCKET_NAME", "bucket")
os.environ.setdefault("URL_SERVICE_TECH", "https://example.com")

botocore_module = types.ModuleType("botocore")
botocore_exceptions = types.ModuleType("botocore.exceptions")


class _ClientError(Exception):
    pass


botocore_exceptions.ClientError = _ClientError
sys.modules.setdefault("botocore", botocore_module)
sys.modules.setdefault("botocore.exceptions", botocore_exceptions)

boto3_module = types.ModuleType("boto3")
boto3_module.client = lambda *args, **kwargs: object()
sys.modules.setdefault("boto3", boto3_module)

from src.domain.entity.certificate import Certificate
from src.domain.entity.order import Order
from src.domain.entity.product import Product
from src.infrastructure.repository.certificate_repository_impl import CertificateRepositoryImpl
from src.infrastructure.repository.order_repository_impl import OrderRepositoryImpl
from src.infrastructure.repository.product_repository_impl import ProductRepositoryImpl


class FakeDynamoDBService:
    pass


class DynamoDBRepositoryDerivationsTestCase(unittest.TestCase):
    def test_certificate_prepare_item_adds_query_keys(self):
        repository = CertificateRepositoryImpl(FakeDynamoDBService())
        certificate = Certificate(
            id=uuid.uuid4(),
            success=True,
            certificate_key="key-1",
            certificate_url="https://example.com/1.pdf",
            generated_date="2025-01-10T10:00:00",
            order_id=1,
            order_date="2025-01-01 10:00:00",
            product_id=100,
            product_name="Curso",
            certificate_details="Detalhes",
            certificate_logo="logo.png",
            certificate_background="background.png",
            participant_email=" User+Test@Example.com ",
            participant_first_name="User",
            participant_last_name="One",
        )

        item = repository._prepare_item(certificate)

        self.assertEqual(item["participant_email"], "user+test@example.com")
        self.assertEqual(item["participant_email_product_key"], "user+test@example.com#100")
        self.assertEqual(item["success_flag"], 1)
        self.assertEqual(item["id"], str(certificate.id))

    def test_order_prepare_item_adds_month_and_sort_key(self):
        repository = OrderRepositoryImpl(FakeDynamoDBService())
        order = Order(
            order_id=25,
            order_date="2025-02-03 14:15:16",
            product_id=99,
            product_name="Curso",
            certificate_details="Detalhes",
            certificate_logo="logo.png",
            certificate_background="background.png",
            time_checkin="13:00",
            participant_email=" Test@Example.com ",
            participant_first_name="Test",
            participant_last_name="User",
        )

        item = repository._prepare_item(order)

        self.assertEqual(item["participant_email"], "test@example.com")
        self.assertEqual(item["order_year_month"], "2025-02")
        self.assertTrue(item["order_date_order_id"].startswith("2025-02-03T14:15:16#"))

    def test_product_prepare_item_adds_boolean_flags(self):
        repository = ProductRepositoryImpl(FakeDynamoDBService())
        product = Product(
            product_id=7,
            product_name="Curso",
            certificate_details="Detalhes",
            certificate_logo="logo.png",
            certificate_background=None,
        )

        item = repository._prepare_item(product)

        self.assertEqual(item["has_certificate_logo_flag"], 1)
        self.assertEqual(item["has_certificate_background_flag"], 0)


if __name__ == "__main__":
    unittest.main()
