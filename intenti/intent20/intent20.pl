intent(containerTrackingIntent, portAuthorityOp, 50000, portTrackingService).

propertyExpectation(cp_port, containerTrackingIntent, logging, cloud, trackingEngineVF, _).
propertyExpectation(bw_port, containerTrackingIntent, bandwidth, greater, hard, 200, megabps, gateway, trackingEngineVF).
propertyExpectation(aff_port, containerTrackingIntent, affinity, dedicated, soft, _, _, signalAggregatorVF, _).

target(portTrackingService, [signalAggregatorVF, trackingEngineVF]).

vnf(signalAggregatorVF, edge, 6).
vnf(trackingEngineVF, cloud, 20).

vnfXUser(signalAggregatorVF, m, (1, 50000), 24).
vnfXUser(trackingEngineVF, l, (1, 50000), 64).
