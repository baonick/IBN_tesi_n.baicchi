intent(smartGridIntent, energyProviderOp, 20000, gridBalancingService).

propertyExpectation(cp_grid, smartGridIntent, caching, _, _, loadAnalyzerVF).
propertyExpectation(lat_grid, smartGridIntent, latency, lower, hard, 20, ms, gateway, loadAnalyzerVF).
propertyExpectation(aff_grid, smartGridIntent, affinity, same, soft, _, _, meterGatewayVF, loadAnalyzerVF).

target(gridBalancingService, [meterGatewayVF, loadAnalyzerVF, gridDbVF]).

vnf(meterGatewayVF, edge, 4).
vnf(loadAnalyzerVF, edge, 15).
vnf(gridDbVF, cloud, 10).

vnfXUser(meterGatewayVF, m, (1, 20000), 16).
vnfXUser(loadAnalyzerVF, l, (1, 20000), 48).
vnfXUser(gridDbVF, m, (1, 20000), 24).
