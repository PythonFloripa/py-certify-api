from aws_lambda_powertools.utilities.typing import LambdaContext
from src.infrastructure.aws.api_gateway_restr_resolver import app
from src.main.presentation.controller import certificate as _certificate_routes

# O import registra as rotas no APIGatewayRestResolver por meio dos decorators.


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
