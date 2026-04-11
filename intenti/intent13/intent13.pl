intent(smartHeatingIntent, gasProviderOp, 100000, heatingManagementService).

propertyExpectation(cp_heat1, smartHeatingIntent, privacy, _, _, billingEngineVF).
propertyExpectation(cp_heat2, smartHeatingIntent, logging, cloud, billingEngineVF, _).
propertyExpectation(bw_heat, smartHeatingIntent, bandwidth, greater, hard, 100, megabps, billingEngineVF, customerDbVF).

target(heatingManagementService, [homeAggregatorVF, consumptionAnalyzerVF, billingEngineVF, customerDbVF]).

vnf(homeAggregatorVF, edge, 6).
vnf(consumptionAnalyzerVF, edge, 18).
vnf(billingEngineVF, cloud, 20).
vnf(customerDbVF, cloud, 15).

vnfXUser(homeAggregatorVF, m, (1, 100000), 24).
vnfXUser(consumptionAnalyzerVF, l, (1, 100000), 64).
vnfXUser(billingEngineVF, l, (1, 100000), 128).
vnfXUser(customerDbVF, m, (1, 100000), 48).
