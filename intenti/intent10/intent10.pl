intent(traficIntent, cityOp, 50000, smartRoutingService).

propertyExpectation(cp_traf, cityTrafficIntent, compression, _, _, routeOptimizerVF).
propertyExpectation(lat_traf, cityTrafficIntent, latency, lower, hard, 15, ms, gateway, routeOptimizerVF).
propertyExpectation(hw_traf, cityTrafficIntent, totChainHW, lower, soft, 100, gb, _, _).

target(smartRoutingService, [vehicleReceiverVF, contextAnalyzerVF, routeOptimizerVF, trafficDbVF]).

vnf(vehicleReceiverVF, edge, 4).
vnf(contextAnalyzerVF, edge, 12).
vnf(routeOptimizerVF, edge, 20).
vnf(trafficDbVF, cloud, 15).

vnfXUser(vehicleReceiverVF, l, (1, 50000), 32).
vnfXUser(contextAnalyzerVF, l, (1, 50000), 64).
vnfXUser(routeOptimizerVF, l, (1, 50000), 128).
vnfXUser(trafficDbVF, m, (1, 50000), 48).
