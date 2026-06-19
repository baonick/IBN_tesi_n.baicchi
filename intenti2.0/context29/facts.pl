intent(saasBillingIntent, subscriptionOp, 50000, saasSubscriptionService).


propertyExpectation(privReq, saasBillingIntent, privacy, _, subscriptionIngesterVF, _).
propertyExpectation(decReq, saasBillingIntent, decoding, _, _, billingCycleProcessorVF).
propertyExpectation(logReq, saasBillingIntent, logging, _, _, dunningManagerVF).
propertyExpectation(encReq, saasBillingIntent, encoding, _, _, invoiceGeneratorVF).

target(saasSubscriptionService, [subscriptionIngesterVF, billingCycleProcessorVF, dunningManagerVF, invoiceGeneratorVF]).

vnf(subscriptionIngesterVF, edge, 12).
vnf(billingCycleProcessorVF, cloud, 24).
vnf(dunningManagerVF, cloud, 16).
vnf(invoiceGeneratorVF, cloud, 16).

vnfXUser(subscriptionIngesterVF, m, (1, 50000), 24).
vnfXUser(billingCycleProcessorVF, l, (1, 50000), 48).
vnfXUser(dunningManagerVF, m, (1, 50000), 32).
vnfXUser(invoiceGeneratorVF, m, (1, 50000), 32).