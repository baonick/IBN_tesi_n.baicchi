intent(autoCheckoutIntent, retailOp, 400, cashierlessService).

propertyExpectation(cp_check, autoCheckoutIntent, security, _, _, paymentProcessorVF).
propertyExpectation(bw_check, autoCheckoutIntent, bandwidth, greater, hard, 200, megabps, itemRecognizerVF, paymentProcessorVF).
propertyExpectation(aff_check, autoCheckoutIntent, affinity, dedicated, soft, _, _, itemRecognizerVF, _).

target(cashierlessService, [cartReceiverVF, itemRecognizerVF, paymentProcessorVF, receiptGeneratorVF, inventoryDbVF]).

vnf(cartReceiverVF, edge, 5).
vnf(itemRecognizerVF, edge, 20).
vnf(paymentProcessorVF, edge, 15).
vnf(receiptGeneratorVF, cloud, 5).
vnf(inventoryDbVF, cloud, 10).

vnfXUser(cartReceiverVF, m, (1, 400), 16).
vnfXUser(itemRecognizerVF, l, (1, 400), 48).
vnfXUser(paymentProcessorVF, l, (1, 400), 32).
vnfXUser(receiptGeneratorVF, s, (1, 400), 8).
vnfXUser(inventoryDbVF, m, (1, 400), 16).
