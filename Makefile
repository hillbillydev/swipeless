PROFILE := "private"

invoke-start-payment-process:
	sam local invoke \
		--event functions/start_payment_process/event.json StartPaymentProcessFunction \
		--profile ${PROFILE}

invoke-purchase:
	sam local invoke \
		--event functions/purchase/event.json PurchaseFunction \
		--profile ${PROFILE}

invoke-purchase-status:
	sam local invoke \
		--event functions/status/event.json StatusFunction \
		--profile ${PROFILE}

invoke-notify-transaction-event:
	sam local invoke \
		--event functions/notify_transaction_event/event.json NotifyTransactionEventFunction \
		--profile ${PROFILE}
