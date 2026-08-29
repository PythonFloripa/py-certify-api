import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.application.dto.list_user_certificates_dto import ListUserCertificatesRequestDto
from src.application.list_user_certificates import ListUserCertificates
from src.domain.entity.certificate import Certificate


class FakeCertificateRepository:
    def __init__(self, certificates):
        self.certificates = certificates
        self.last_email = None

    def get_by_participant_email(self, email: str):
        self.last_email = email
        return list(self.certificates)


class ListUserCertificatesTestCase(unittest.TestCase):
    def setUp(self):
        self.email = "user@example.com"
        self.encoded_email = "user+qa@example.com"
        self.certificates = [
            self._certificate(
                generated_date="2025-01-10T10:00:00",
                success=True,
                order_id=1,
            ),
            self._certificate(
                generated_date=None,
                success=True,
                order_id=2,
            ),
            self._certificate(
                generated_date="2025-01-12T09:30:00",
                success=False,
                order_id=3,
            ),
            self._certificate(
                generated_date="2025-01-11T08:00:00",
                success=True,
                order_id=4,
            ),
        ]

    def test_lists_all_certificates_sorted_by_generated_date_desc(self):
        service = ListUserCertificates(FakeCertificateRepository(self.certificates))

        response = service.execute(ListUserCertificatesRequestDto(email=self.email))

        self.assertEqual(response.email, self.email)
        self.assertEqual([item.order_id for item in response.certificates], [3, 4, 1, 2])

    def test_filters_success_true_before_sorting(self):
        service = ListUserCertificates(FakeCertificateRepository(self.certificates))

        response = service.execute(
            ListUserCertificatesRequestDto(email=self.email, success=True)
        )

        self.assertEqual([item.order_id for item in response.certificates], [4, 1, 2])
        self.assertTrue(all(item.success is True for item in response.certificates))

    def test_filters_success_false(self):
        service = ListUserCertificates(FakeCertificateRepository(self.certificates))

        response = service.execute(
            ListUserCertificatesRequestDto(email=self.email, success=False)
        )

        self.assertEqual([item.order_id for item in response.certificates], [3])
        self.assertEqual(response.certificates[0].success, False)

    def test_returns_empty_list_when_no_records_match_email(self):
        service = ListUserCertificates(FakeCertificateRepository([]))

        response = service.execute(ListUserCertificatesRequestDto(email=self.email))

        self.assertEqual(response.email, self.email)
        self.assertEqual(response.certificates, [])

    def test_returns_empty_list_when_status_filter_has_no_matches(self):
        only_successful = [
            self._certificate(
                generated_date="2025-01-10T10:00:00",
                success=True,
                order_id=10,
            )
        ]
        service = ListUserCertificates(FakeCertificateRepository(only_successful))

        response = service.execute(
            ListUserCertificatesRequestDto(email=self.email, success=False)
        )

        self.assertEqual(response.email, self.email)
        self.assertEqual(response.certificates, [])

    def test_preserves_email_value_used_in_lookup(self):
        repository = FakeCertificateRepository([])
        service = ListUserCertificates(repository)

        response = service.execute(ListUserCertificatesRequestDto(email=self.encoded_email))

        self.assertEqual(repository.last_email, self.encoded_email)
        self.assertEqual(response.email, self.encoded_email)

    def _certificate(self, generated_date, success, order_id):
        return Certificate(
            id=uuid.uuid4(),
            success=success,
            certificate_key=f"key-{order_id}",
            certificate_url=f"https://example.com/{order_id}.pdf",
            generated_date=generated_date,
            order_id=order_id,
            order_date="2025-01-01 10:00:00",
            product_id=100 + order_id,
            product_name="Curso",
            certificate_details="Detalhes",
            certificate_logo="logo.png",
            certificate_background="background.png",
            participant_email=self.email,
            participant_first_name="User",
            participant_last_name=str(order_id),
        )


if __name__ == "__main__":
    unittest.main()
