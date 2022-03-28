import requests
import xml.etree.ElementTree as ET
import os

from typing import Any, Dict
from aws_lambda_powertools.utilities.typing import LambdaContext

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics()
tracer = Tracer()

windcave_url = os.getenv("WINDCAVE_URL")

class PaymentStatusException(Exception):
    def __init__(self, message=None, details=None):
        self.message = message or "Payment status failed"
        self.details = details or {}


@tracer.capture_method
def make_payment_status(transaction_reference, user, key, station_id):
    try:
        logger.debug(
            {
                "operation": "payment_status",
                "details": {
                    "transaction_reference": transaction_reference,
                    "user":  user,
                    "station_id": station_id
                }
            }
        )

        body = f"""
        <Scr action="doScrHIT" user="{user}" key="{key}">
        <TxnType>Status</TxnType>
        <TxnRef>{transaction_reference}</TxnRef>
        <Station>{station_id}</Station>
        </Scr>
        """

        res = requests.post(windcave_url, body)
        res.raise_for_status()

        logger.info({"operation": "payment", "details": res})
        tracer.put_metadata(transaction_reference, res.text)

        return res

    except requests.exceptions.RequestException as err:
        raise PaymentStatusException(details=err)


@ metrics.log_metrics(capture_cold_start_metric=True)
@ logger.inject_lambda_context(log_event=True)
@ tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:

    transaction_reference = event.get('transactionReference')
    station_id = 1
    user = "ask_username"
    key = "ask_for_key"

    try:
        res = make_payment_status(transaction_reference, user, key, station_id)

        tracer.put_metadata(transaction_reference, res.text)

        logger.info(
            {
                "operation": "payment_status",
                "details": {
                    "response_headers": res.headers,
                    "response_payload": res.text,
                    "response_status_code": res.status_code,
                    "url": res.url
                },
            }
        )
        root = ET.fromstring(res.text)

        return {
            "transactionReference": root.findtext("TxnRef"),
            "terminalStep": root.findtext("TxnStatusId", 'done'), # TODO fix me.
            "done": root.findtext("Complete") == "1"
        }

    except PaymentStatusException as err:
        metrics.add_metric(name="FailedPaymentStatusCheck", unit=MetricUnit.Count, value=1)
        tracer.put_annotation("PaymentStatusCheck", "FAILED")
        logger.exception({"operation": "payment_status"})
        raise
