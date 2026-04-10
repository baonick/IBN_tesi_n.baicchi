intent(busFleetIntent, transitOp, 500, autonomousBusService).

propertyExpectation(cp_bus, busFleetIntent, security, _, _, pathCoordinatorVF).
propertyExpectation(hw_bus, busFleetIntent, totChainHW, lower, hard, 64, gb, _, _).
propertyExpectation(av_bus, busFleetIntent, chainAvailability, greater, soft, 0.9999, _, _, _).

target(autonomousBusService, [vehicleReceiverVF, pathCoordinatorVF, fleetRegistryVF]).

vnf(vehicleReceiverVF, edge, 3).
vnf(pathCoordinatorVF, edge, 12).
vnf(fleetRegistryVF, cloud, 8).

vnfXUser(vehicleReceiverVF, s, (1, 500), 8).
vnfXUser(pathCoordinatorVF, m, (1, 500), 24).
vnfXUser(fleetRegistryVF, s, (1, 500), 12).
