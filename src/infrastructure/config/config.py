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
    def dynamodb_table(self) -> Dict[str, str]:
        """
        Retorna a configuração da tabela única do DynamoDB baseada no ambiente.
        Single Table Design - todas as entidades em uma única tabela.
        """
        base_name = f"{self.PROJECT_NAME}"
        environment = self.ENVIRONMENT
        
        return {
            "name": f"{base_name}-{environment}",
            "arn": f"arn:aws:dynamodb:{self.REGION}:*:table/{base_name}-{environment}"
        }
    
    @property
    def dynamodb_tables(self) -> Dict[str, Dict[str, str]]:
        return {"single": self.dynamodb_table}
    
    def get_table_name(self, entity: str = None) -> str:
        return self.dynamodb_table["name"]
    
    def get_table_arn(self, entity: str = None) -> str:
        return self.dynamodb_table["arn"]


config = Config()

