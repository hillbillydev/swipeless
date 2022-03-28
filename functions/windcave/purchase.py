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

class PaymentException(Exception):
    def __init__(self, message=None, details=None):
        self.message = message or "Payment failed"
        self.details = details or {}

@tracer.capture_method
def make_payment(transaction_reference: str, user: str, key:str, register_id: str, currency: str, amount: float, station_id: int):
    try:
        logger.debug({"operation": "payment", "details": {
            "register_id": register_id,
            "windcave_url": windcave_url,
            "transaction_reference": transaction_reference,
            "amount": amount
        }})

        # Windcave has an constraint on dashes, let's strip them.
        device_id = register_id.replace("-", "")

        body = f"""
        <Scr action="doScrHIT" user="{user}" key="{key}">
        <TxnType>Purchase</TxnType>
        <Amount>{amount}</Amount>
        <TxnRef>{transaction_reference}</TxnRef>
        <Cur>{currency}</Cur>
        <Station>{station_id}</Station>
        <DeviceId>{device_id}</DeviceId>
        <PosName>Vend</PosName>
        <VendorId>1</VendorId>
        </Scr>
        """

        res = requests.post(windcave_url, body)
        res.raise_for_status()

        logger.info({"operation": "payment", "details": res})
        tracer.put_metadata(transaction_reference, res)

        return res

    except requests.exceptions.RequestException as err:
        raise PaymentException(details=err)


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:

    transaction_reference = event.get('transactionReference')
    register_id = event.get('registerId')
    currency = "NZD"
    amount = event.get('amount')

    user = "ask_username"
    key = "ask_for_key"
    station_id = 1

    try:
        res = make_payment(transaction_reference, user, key, register_id, currency, amount, station_id)

        tracer.put_metadata(transaction_reference, res.text)

        logger.info(
            {
                "operation": "payment",
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
            "terminalStep": root.findtext("TxnStatusId"),
            "done": root.findtext("Complete") == "1"
        }

    except PaymentException as err:
        metrics.add_metric(name="FailedPayment", unit=MetricUnit.Count, value=1)
        tracer.put_annotation("PaymentStatus", "FAILED")
        logger.exception({"operation": "payment"})
        raise
