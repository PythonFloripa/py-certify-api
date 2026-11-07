from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app: APIGatewayRestResolver = APIGatewayRestResolver(
    enable_validation=True,
)
