import logging
from datetime import datetime

from src.application.dto.list_user_certificates_dto import (
    ListUserCertificatesRequestDto,
    ListUserCertificatesResponseDto,
    UserCertificateItemDto,
)
from src.domain.entity.certificate import Certificate
from src.domain.repository.certificate_repository import CertificateRepository


logger = logging.getLogger(__name__)


class ListUserCertificates:
    def __init__(self, certificate_repository: CertificateRepository | None = None):
        if certificate_repository is None:
            from src.infrastructure.container.dependency_container import container

            certificate_repository = container.get("certificate_repository")

        self.certificate_repository = certificate_repository

    def execute(self, request: ListUserCertificatesRequestDto) -> ListUserCertificatesResponseDto:
        logger.info(
            "Listing certificates for email=%s success=%s",
            request.email,
            request.success,
        )

        certificates = self.certificate_repository.get_by_participant_email(request.email)

        if request.success is not None:
            certificates = [
                certificate for certificate in certificates if certificate.success is request.success
            ]

        sorted_certificates = sorted(
            certificates,
            key=self._sort_key,
            reverse=True,
        )

        return ListUserCertificatesResponseDto(
            email=request.email,
            certificates=[self._to_item_dto(certificate) for certificate in sorted_certificates],
        )

    def _to_item_dto(self, certificate: Certificate) -> UserCertificateItemDto:
        return UserCertificateItemDto(
            id=str(certificate.id),
            order_id=certificate.order_id,
            product_id=certificate.product_id,
            participant_name=f"{certificate.participant_first_name or ''} {certificate.participant_last_name or ''}".strip(),
            participant_email=certificate.participant_email,
            certificate_url=certificate.certificate_url,
            created_at=certificate.generated_date,
            updated_at=certificate.generated_date,
            success=certificate.success,
        )

    def _sort_key(self, certificate: Certificate) -> tuple[bool, datetime]:
        generated_at = self._parse_generated_date(certificate.generated_date)
        return generated_at is not None, generated_at or datetime.min

    def _parse_generated_date(self, value: str | None) -> datetime | None:
        if not value:
            return None

        normalized_value = value.replace("Z", "+00:00")

        try:
            return datetime.fromisoformat(normalized_value)
        except ValueError:
            pass

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        logger.warning("Unable to parse generated_date=%s for sorting", value)
        return None
