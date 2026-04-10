intent(droneDeliveryIntent, logisticsOp, 800, droneRoutingService).

propertyExpectation(cp_drone, droneDeliveryIntent, compression, _, _, routeOptimizerVF).
propertyExpectation(av_drone, droneDeliveryIntent, chainAvailability, greater, hard, 0.999, _, _, _).
propertyExpectation(aff_drone, droneDeliveryIntent, affinity, dedicated, soft, _, _, routeOptimizerVF, _).

target(droneRoutingService, [flightReceiverVF, routeOptimizerVF, shippingArchiveVF]).

vnf(flightReceiverVF, edge, 4).
vnf(routeOptimizerVF, edge, 15).
vnf(shippingArchiveVF, cloud, 8).

vnfXUser(flightReceiverVF, s, (1, 800), 8).
vnfXUser(routeOptimizerVF, l, (1, 800), 32).
vnfXUser(shippingArchiveVF, m, (1, 800), 16).
