import logging
from typing import List
from retry import retry
from src.infrastructure.aws.sqs_service import SQSService
from src.domain.response.tech_floripa import TechOrdersResponse


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SendForBuildCertificate:
    def __init__(self, sqs_service: SQSService):
        self.sqs_service = sqs_service
        self.parts = 30

    def execute(self, orders: List[TechOrdersResponse]):
        processed_orders = self.__processed_orders_dict(orders)
        for part in processed_orders:
            self.__send_to_sqs(part)

    def __processed_orders_dict(
        self, orders: List[TechOrdersResponse]
    ) -> List[List[dict]]:
        # Divide as ordens em partes para enviar para a fila de build de certificado,
        parts = []
        for i in range(0, len(orders), self.parts):
            parts.append([order.model_dump() for order in orders[i : i + self.parts]])
        return parts

    @retry(exceptions=Exception, tries=2, delay=2, backoff=2, logger=logger)
    def __send_to_sqs(self, orders: List[dict]):
        try:
            logger.info(f"Sending {len(orders)} orders to build certificate.")
            self.sqs_service.send_message(orders)
            logger.info("Orders sent to build certificate.")
        except Exception as e:
            logger.error(f"Error sending orders to build certificate: {e}")
            raise e
