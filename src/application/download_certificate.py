import logging
from src.domain.repository.certificate_repository import CertificateRepository
from src.application.dto.download_certificate_dto import (
    DownloadCertificateRequestDto,
    DownloadCertificateResponseDto,
)
from src.infrastructure.container.dependency_container import container
from src.infrastructure.aws.file_manager import FileManager
from src.domain.exception.certificate_not_found import CertificateNotFound

logger = logging.getLogger(__name__)


class DownloadCertificate:
    def __init__(self):
        self.certificate_repository: CertificateRepository = container.get(
            "certificate_repository"
        )
        self.file_manager: FileManager = container.get("file_manager")

    def execute(
        self, request: DownloadCertificateRequestDto
    ) -> DownloadCertificateResponseDto:
        logger.info(f"Buscando certificado para download com ID: {request.id}")

        certificate = self.certificate_repository.find_by_id(request.id)

        if not certificate:
            raise CertificateNotFound(
                f"Certificado não encontrado para ID: {request.id}"
            )

        certificate_url = ""

        if certificate.success and certificate.certificate_key:
            certificate_url = self.file_manager.get_certificate_download_url(
                certificate.certificate_key
            )
            logger.info(f"URL pré-assinada gerada para certificado {request.id}")
        elif certificate.success and not certificate.certificate_key:
            logger.warning(
                f"Certificado {request.id} marcado como sucesso mas sem certificate_key"
            )
        elif not certificate.success:
            logger.info(f"Certificado {request.id} não foi processado com sucesso")

        return DownloadCertificateResponseDto(
            certificate_url=certificate_url,
            email=certificate.participant_email or "",
            product_id=certificate.product_id,
            success=certificate.success or False,
        )
