import logging
from pydantic_settings import BaseSettings
from typing import Dict
from pydantic import Field

logger = logging.getLogger(__name__)


class Config(BaseSettings):
    REGION: str
    BUILDER_QUEUE_URL: str
    S3_BUCKET_NAME: str
    ENVIRONMENT: str = Field(default="dev")
    PROJECT_NAME: str = Field(default="certified-builder-api-py")
    URL_SERVICE_TECH: str
    PREFIX_API_VERSION: str = Field(default="/api/v1")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def dynamodb_tables(self) -> Dict[str, Dict[str, str]]:
        """
        Retorna as configurações das tabelas do DynamoDB baseadas no ambiente.
        Segue o padrão da infraestrutura Terraform criada.
        """
        base_name = f"{self.PROJECT_NAME}"
        environment = self.ENVIRONMENT

        return {
            "certificates": {
                "name": f"{base_name}-certificates-{environment}",
                "arn": f"arn:aws:dynamodb:{self.REGION}:*:table/{base_name}-certificates-{environment}",
            },
            "orders": {
                "name": f"{base_name}-orders-{environment}",
                "arn": f"arn:aws:dynamodb:{self.REGION}:*:table/{base_name}-orders-{environment}",
            },
            "participants": {
                "name": f"{base_name}-participants-{environment}",
                "arn": f"arn:aws:dynamodb:{self.REGION}:*:table/{base_name}-participants-{environment}",
            },
            "products": {
                "name": f"{base_name}-products-{environment}",
                "arn": f"arn:aws:dynamodb:{self.REGION}:*:table/{base_name}-products-{environment}",
            },
        }

    def get_table_name(self, entity: str) -> str:
        """
        Retorna o nome da tabela para uma entidade específica.

        Args:
            entity: Nome da entidade (certificates, orders, participants, products)

        Returns:
            str: Nome da tabela no DynamoDB
        """
        tables = self.dynamodb_tables
        if entity not in tables:
            raise ValueError(
                f"Entidade '{entity}' não encontrada. Entidades disponíveis: {list(tables.keys())}"
            )

        return tables[entity]["name"]

    def get_table_arn(self, entity: str) -> str:
        """
        Retorna o ARN da tabela para uma entidade específica.

        Args:
            entity: Nome da entidade (certificates, orders, participants, products)

        Returns:
            str: ARN da tabela no DynamoDB
        """
        tables = self.dynamodb_tables
        if entity not in tables:
            raise ValueError(
                f"Entidade '{entity}' não encontrada. Entidades disponíveis: {list(tables.keys())}"
            )

        return tables[entity]["arn"]


config = Config()
