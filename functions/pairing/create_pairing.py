import os
import json
from typing import Any, Dict

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics()
tracer = Tracer()

windcave_url = os.getenv('SWIPELESS_TABLE')

def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    username = event.get('username')
    register_id = event.get('apiKey')
    amount = event.get('stationId')

    return json.dumps({
        username: username,
        register_id: register_id,
        amount: amount
    })
