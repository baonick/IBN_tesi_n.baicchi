intent(rescueSwarmIntent, emergencyOp, 300, droneRescueService).

propertyExpectation(cp_swarm, rescueSwarmIntent, caching, _, _, mappingEngineVF).
propertyExpectation(av_swarm, rescueSwarmIntent, chainAvailability, greater, hard, 0.9999, _, _, _).
propertyExpectation(lat_swarm, rescueSwarmIntent, latency, lower, hard, 8, ms, gateway, swarmCoordinatorVF).

target(droneRescueService, [telemetryReceiverVF, swarmCoordinatorVF, mappingEngineVF, missionLogVF]).

vnf(telemetryReceiverVF, edge, 3).
vnf(swarmCoordinatorVF, edge, 15).
vnf(mappingEngineVF, edge, 25).
vnf(missionLogVF, cloud, 5).

vnfXUser(telemetryReceiverVF, s, (1, 300), 8).
vnfXUser(swarmCoordinatorVF, m, (1, 300), 24).
vnfXUser(mappingEngineVF, l, (1, 300), 48).
vnfXUser(missionLogVF, s, (1, 300), 12).
