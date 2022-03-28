import boto3
import os
from typing import Any, Dict

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
metrics = Metrics()
tracer = Tracer()

#dynamodb = boto3.resource('dynamodb')
#table = dynamodb.Table(os.getenv("CONNECTION_TABLE"))

@ metrics.log_metrics(capture_cold_start_metric=True)
@ logger.inject_lambda_context(log_event=True)
@ tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    return {
        "statusCode": 200,
        "body": "Disconnected."
    }
