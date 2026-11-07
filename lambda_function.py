from aws_lambda_powertools.utilities.typing import LambdaContext
from src.infrastructure.aws.api_gateway_restr_resolver import app

# Importa os controladores para registrar as rotas


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
