from typing import Optional


class InvalidCertificateBackground(Exception):
    """O fundo do certificado não segue o padrão Tech Floripa (1200x627, PNG ou JPG)."""

    def __init__(self, message: str, url: Optional[str] = None):
        self.message = message
        self.url = url
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return self.message
