import json
import logging
from botocore.exceptions import ClientError
from typing import Dict, List

from src.infrastructure.aws.boto_aws import get_instance_aws, ServiceNameAWS
from src.infrastructure.config.config import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SQSService:
    def __init__(self):
        self.aws = get_instance_aws(ServiceNameAWS.SQS)
        self.queue_url = config.BUILDER_QUEUE_URL

    def send_message(self, messagens: List[Dict]):
        try:
            logger.info(
                f"Enviando mensagem para a fila {self.queue_url} com {len(messagens)} mensagens"
            )
            response = self.aws.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(messagens),
            )
            logger.info(f"Mensagem enviada com sucesso: {response['MessageId']}")
            return response
        except ClientError as e:
            logger.error(
                f"Erro ao enviar mensagem para a fila {self.queue_url}: {str(e)}"
            )
            raise
