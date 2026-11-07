import logging
from typing import List, Optional
from src.domain.response.tech_floripa import TechOrdersResponse
from src.domain.response.processed_orders import ProcessedOrdersResponse
from src.application.mapper.tech_order import (
    TechOrderMapper,
    TechProductMapper,
    TechParticipantMapper,
    CertificateMapper,
)

from src.domain.repository.certificate_repository import CertificateRepository
from src.domain.repository.participant_repository import ParticipantRepository
from src.domain.repository.product_repository import ProductRepository
from src.domain.repository.order_repository import OrderRepository

from src.infrastructure.container.dependency_container import container

logger = logging.getLogger()


class CreateCertificate:
    def __init__(self):
        self.certificate_repository: CertificateRepository = container.get(
            "certificate_repository"
        )
        self.participant_repository: ParticipantRepository = container.get(
            "participant_repository"
        )
        self.product_repository: ProductRepository = container.get("product_repository")
        self.order_repository: OrderRepository = container.get("order_repository")

    def execute(self, tech_orders: List[TechOrdersResponse]) -> ProcessedOrdersResponse:
        logger.info(
            f"Starting certificate creation process for tech orders size: {len(tech_orders)}."
        )

        if len(tech_orders) == 0:
            logger.info("No tech orders provided, skipping certificate creation.")
            return ProcessedOrdersResponse(valid_orders=[], invalid_orders=[])
        # Valida e processa as ordens
        valid_orders, invalid_orders = self.__validate_tech_orders_with_time_checkin(
            tech_orders
        )

        # Processa as ordens válidas
        processed_orders = []
        for order in valid_orders:
            try:
                processed_order = self.__register_certificate(order)
                if processed_order:
                    processed_orders.append(processed_order)
            except Exception as e:
                logger.error(f"Error processing order {order.order_id}: {str(e)}")

        logger.info(f"Successfully processed {len(processed_orders)} certificates.")

        return ProcessedOrdersResponse(
            valid_orders=processed_orders,
            invalid_orders=invalid_orders,
        )

    def __validate_tech_orders_with_time_checkin(
        self, tech_orders: List[TechOrdersResponse]
    ) -> tuple[List[TechOrdersResponse], List[int]]:
        logger.info("Processing tech orders to create certificates.")

        valid_orders = []
        invalid_orders = []

        for order in tech_orders:
            if not order.is_empty_time_checkin():
                valid_orders.append(order)
            else:
                invalid_orders.append(order)

        logger.info(f"Processed {len(valid_orders)} valid orders.")
        logger.info(f"Processed {len(invalid_orders)} invalid orders.")

        if invalid_orders:
            logger.warning("Some tech orders are invalid and will be skipped.")

        return valid_orders, invalid_orders

    def __register_certificate(
        self, order: TechOrdersResponse
    ) -> Optional[TechOrdersResponse]:

        logger.info(
            f"Registering certificate for order ID: {order.order_id} and product ID: {order.product_id}."
        )

        try:
            # Mapeia os dados da ordem técnica para entidades
            order_entity = TechOrderMapper.to_entity(order)
            product_entity = TechProductMapper.to_entity(order)
            participant_entity = TechParticipantMapper.to_entity(order)

            # Verifica se existe um certificado para a ordem
            certificate_exist = self.certificate_repository.get_by_order_id(
                order.order_id
            )
            if certificate_exist and len(certificate_exist) > 0:
                if certificate_exist[0].success:
                    logger.info(
                        f"Certificate already exists for order {order.order_id}, skipping certificate creation."
                    )
                    return None

            # Verifica se o participante já existe
            participant_exist = self.participant_repository.get_by_email(order.email)
            if not participant_exist:
                logger.info(
                    f"Participant not exists for order {order.order_id}, creating new participant."
                )
                self.participant_repository.create(participant_entity)
            else:
                logger.info(
                    f"Participant already exists for order {order.order_id}, skipping participant."
                )

            product_exist = self.product_repository.get_by_id(order.product_id)
            if not product_exist:
                logger.info(
                    f"Product not exists for order {order.order_id}, creating new product."
                )
                self.product_repository.create(product_entity)
            else:
                logger.info(
                    f"Product already exists for order {order.order_id}, skipping product."
                )

            order_exist = self.order_repository.get_by_id(order.order_id)
            if not order_exist:
                logger.info(
                    f"Order not exists for order {order.order_id}, creating new order."
                )
                self.order_repository.create(order_entity)
            else:
                logger.info(
                    f"Order already exists for order {order.order_id}, skipping order."
                )

            certificate_entity = CertificateMapper.to_entity(order)
            certificate_exist = self.certificate_repository.get_by_order_id(
                certificate_entity.order_id
            )
            if not certificate_exist or len(certificate_exist) == 0:
                logger.info(
                    f"Certificate not exists for order {order.order_id}, creating new certificate."
                )
                self.certificate_repository.create(certificate_entity)
            else:
                logger.info(
                    f"Certificate already exists for order {order.order_id}, skipping certificate creation."
                )
                # Não atualiza o certificado existente, apenas pula

            return order

        except Exception as e:
            logger.error(
                f"Error registering certificate for order {order.order_id}: {str(e)}"
            )
            raise
