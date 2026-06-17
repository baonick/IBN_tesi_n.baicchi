intent(droneControlIntent, aeroDeliveryOp, 5000, droneFleetControlService).

propertyExpectation(hwReq, droneControlIntent, totChainHW, lower, soft, 200, gb, _, _).
propertyExpectation(latReq, droneControlIntent, latency, lower, hard, 10, ms, flightTelemetryIngesterVF, collisionAvoiderVF).
propertyExpectation(bwReq, droneControlIntent, bandwidth, higher, soft, 2000, mbps, collisionAvoiderVF, routeDispatcherVF).

propertyExpectation(cachReq, droneControlIntent, caching, _, flightTelemetryIngesterVF, _).

target(droneFleetControlService, [flightTelemetryIngesterVF, collisionAvoiderVF, commandPrioritizerVF, routeDispatcherVF]).

vnf(flightTelemetryIngesterVF, edge, 12).
vnf(collisionAvoiderVF, cloud, 32).
vnf(commandPrioritizerVF, cloud, 16).
vnf(routeDispatcherVF, edge, 12).

vnfXUser(flightTelemetryIngesterVF, m, (1, 5000), 24).
vnfXUser(collisionAvoiderVF, l, (1, 5000), 64).
vnfXUser(commandPrioritizerVF, m, (1, 5000), 32).
vnfXUser(routeDispatcherVF, s, (1, 5000), 12).