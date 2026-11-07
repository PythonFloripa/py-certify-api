from boto3 import client
from enum import Enum
from src.infrastructure.config.config import config


class ServiceNameAWS(Enum):
    SQS = "sqs"
    DYNAMODB = "dynamodb"
    S3 = "s3"


def get_instance_aws(service_name: ServiceNameAWS):
    return client(service_name.value, region_name=config.REGION)
