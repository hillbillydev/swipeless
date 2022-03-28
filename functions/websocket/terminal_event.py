import boto3
import os
import json

from typing import Any, Dict
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from botocore.exceptions import ClientError

logger = Logger()
metrics = Metrics()
tracer = Tracer()

endpoint = os.getenv("PAYMENT_WEBSOCKET_API_URL")
# TODO fix this
client = boto3.client('apigatewaymanagementapi',
                      endpoint_url="https://8loidh8sie.execute-api.ap-southeast-2.amazonaws.com/v1")
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv("CONNECTION_TABLE"))


@ metrics.log_metrics(capture_cold_start_metric=True)
@ logger.inject_lambda_context(log_event=True)
@ tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    message = json.loads(event['Records'][0]['Sns']['Message'])
    transaction_reference = message.get('transactionReference')

    try:
      res = table.get_item(Key={'transactionReference': transaction_reference})
      logger.info(res)

      connection_id = res.get('Item').get('connectionId')
      client.post_to_connection(ConnectionId=connection_id, Data=json.dumps(message))

    except ClientError as e:
        print(e.response['Error']['Message'])
        raise
    except Exception as err:
        print(err)
        raise
