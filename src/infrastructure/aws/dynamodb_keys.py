from enum import Enum
from typing import Optional


class EntityType(str, Enum):
    ORDER = "ORDER"
    PRODUCT = "PRODUCT"
    PARTICIPANT = "PARTICIPANT"
    CERTIFICATE = "CERTIFICATE"


def pk(entity_type: EntityType, entity_id: str | int) -> str:
    return f"{entity_type.value}#{entity_id}"


def sk(entity_type: EntityType, entity_id: str | int) -> str:
    return f"{entity_type.value}#{entity_id}"


def sk_order(order_id: int) -> str:
    return sk(EntityType.ORDER, order_id)


def sk_product(product_id: int) -> str:
    return sk(EntityType.PRODUCT, product_id)


def sk_participant(participant_id: str) -> str:
    return sk(EntityType.PARTICIPANT, participant_id)


def sk_certificate(order_id: int) -> str:
    return sk(EntityType.CERTIFICATE, order_id)


def gsi1pk_email(email: str) -> str:
    return f"EMAIL#{email.lower().strip()}"


def gsi1sk_participant(participant_id: str) -> str:
    return f"PARTICIPANT#{participant_id}"


def gsi1sk_order(order_id: int) -> str:
    return f"ORDER#{order_id}"


def gsi1sk_certificate(order_id: int) -> str:
    return f"CERTIFICATE#{order_id}"


def gsi2pk_product(product_id: int) -> str:
    return f"PRODUCT#{product_id}"


def gsi2sk_order(order_id: int) -> str:
    return f"ORDER#{order_id}"


def gsi2sk_certificate(order_id: int) -> str:
    return f"CERTIFICATE#{order_id}"


def gsi3pk_success(success: bool) -> str:
    return f"SUCCESS#{1 if success else 0}"


def gsi3sk_certificate(order_id: int) -> str:
    return f"CERTIFICATE#{order_id}"


def gsi4pk_city(city: str) -> str:
    return f"CITY#{city}"


def gsi4sk_participant(participant_id: str) -> str:
    return f"PARTICIPANT#{participant_id}"


def gsi1pk_cert_id(cert_id: str) -> str:
    return f"CERT#{cert_id}"


def gsi1sk_cert(cert_id: str) -> str:
    return f"CERTIFICATE#{cert_id}"


def parse_pk(pk: str) -> tuple[EntityType, str]:
    parts = pk.split("#", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid PK format: {pk}")
    return EntityType(parts[0]), parts[1]


def parse_sk(sk: str) -> tuple[EntityType, str]:
    return parse_pk(sk)
