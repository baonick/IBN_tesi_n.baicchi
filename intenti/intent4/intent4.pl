intent(soilIntent, farmOp, 10000, soilMonitoringService).

propertyExpectation(cp_soil, soilIntent, logging, cloud, moistureAnalyzerVF, _).
propertyExpectation(hw_soil, soilIntent, totChainHW, lower, hard, 32, gb, _, _).
propertyExpectation(lat_soil, soilIntent, latency, lower, soft, 50, ms, gateway, moistureAnalyzerVF).

target(soilMonitoringService, [agriAggregatorVF, moistureAnalyzerVF, cropDbVF]).

vnf(agriAggregatorVF, edge, 2).
vnf(moistureAnalyzerVF, edge, 8).
vnf(cropDbVF, cloud, 5).

vnfXUser(agriAggregatorVF, s, (1, 10000), 8).
vnfXUser(moistureAnalyzerVF, m, (1, 10000), 16).
vnfXUser(cropDbVF, m, (1, 10000), 16).
