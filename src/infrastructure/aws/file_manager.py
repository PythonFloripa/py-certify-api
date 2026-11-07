import logging
from src.infrastructure.aws.boto_aws import get_instance_aws, ServiceNameAWS
from src.infrastructure.config.config import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FileManager:
    """
    Gerencia operações de arquivos no S3.
    """

    def __init__(self):
        self.aws = get_instance_aws(ServiceNameAWS.S3)
        self.bucket_name = config.S3_BUCKET_NAME

    def get_url(self, key: str, expires_in: int = 604800) -> str:
        """
        Gera uma URL pré-assinada para acessar (GET) um objeto no S3.
        Configura response-content-disposition=inline para visualização direta no navegador.

        Args:
            key: Chave do objeto no S3
            expires_in: Tempo de expiração em segundos (padrão: 7 dias)

        Returns:
            URL pré-assinada para acesso ao objeto

        Raises:
            Exception: Se houver erro ao gerar a URL
        """
        try:
            logger.info(
                f"Getting URL for key {key} with expiration {expires_in} seconds"
            )

            # Gera URL pré-assinada para GET com response-content-disposition=inline
            presigned_url = self.aws.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "ResponseContentDisposition": "inline",
                },
                ExpiresIn=expires_in,
            )

            logger.info(f"Successfully retrieved URL for key {key}")
            return presigned_url

        except Exception as e:
            logger.error(f"Error generating presigned URL for key {key}: {e}")
            return None

    def get_certificate_download_url(self, certificate_key: str) -> str:
        """
        Gera URL pré-assinada específica para download de certificados.
        URL válida por 30 minutos.

        Args:
            certificate_key: Chave do certificado no S3

        Returns:
            URL pré-assinada para download do certificado (válida por 30 minutos)
        """
        return self.get_url(certificate_key, expires_in=1800)  # 30 minutos em segundos
