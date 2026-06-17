intent(routeOptIntent, deliveryLogisticsOp, 15000, routeOptimizationService).

propertyExpectation(latReq, routeOptIntent, latency, lower, hard, 50, ms, begin, end).

propertyExpectation(compReq, routeOptIntent, compression, _, gpsIngesterVF, _).
propertyExpectation(decReq, routeOptIntent, decoding, _, _, terminalUpdaterVF).

target(routeOptimizationService, [gpsIngesterVF, trafficAnalyzerVF, routeOptimizerVF, terminalUpdaterVF]).

vnf(gpsIngesterVF, edge, 8).
vnf(trafficAnalyzerVF, cloud, 24).
vnf(routeOptimizerVF, cloud, 32).
vnf(terminalUpdaterVF, edge, 12).

vnfXUser(gpsIngesterVF, s, (1, 15000), 16).
vnfXUser(trafficAnalyzerVF, l, (1, 15000), 48).
vnfXUser(routeOptimizerVF, l, (1, 15000), 64).
vnfXUser(terminalUpdaterVF, m, (1, 15000), 24).