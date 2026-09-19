import logging
from io import BytesIO
from typing import Iterable

import httpx
from PIL import Image, UnidentifiedImageError

from src.domain.exception.invalid_certificate_background import InvalidCertificateBackground

logger = logging.getLogger(__name__)

# O builder posiciona nome, logo, QR e código em pixels fixos para este tamanho.
REQUIRED_SIZE = (1200, 627)
ALLOWED_FORMATS = {"PNG", "JPEG"}


class ValidateCertificateBackground:
    """
    Confere, antes de gravar e enfileirar o lote, se o fundo do certificado segue
    o padrão Tech Floripa. Cada URL distinta é baixada uma única vez.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def execute(self, backgrounds: Iterable[str]) -> None:
        for url in dict.fromkeys(backgrounds):
            self.__validate(url)

    def __validate(self, url: str) -> None:
        if not url or not url.strip():
            raise InvalidCertificateBackground(
                "Fundo do certificado não informado. Cadastre no evento a URL de uma "
                "imagem PNG ou JPG de exatamente 1200×627 px."
            )

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
            image = Image.open(BytesIO(response.content))
        except (httpx.HTTPError, UnidentifiedImageError) as e:
            logger.warning(f"Fundo do certificado inacessível ou ilegível ({url}): {e}")
            raise InvalidCertificateBackground(
                f"Não foi possível baixar ou abrir o fundo do certificado ({url}). "
                "Confira se a URL aponta para uma imagem PNG ou JPG pública.",
                url=url,
            )

        if image.format not in ALLOWED_FORMATS:
            raise InvalidCertificateBackground(
                f"Fundo do certificado em formato {image.format}; use PNG ou JPG.",
                url=url,
            )

        if image.size != REQUIRED_SIZE:
            width, height = image.size
            raise InvalidCertificateBackground(
                f"Fundo do certificado com {width}×{height} px; o padrão Tech Floripa "
                f"exige exatamente {REQUIRED_SIZE[0]}×{REQUIRED_SIZE[1]} px (PNG ou JPG).",
                url=url,
            )
