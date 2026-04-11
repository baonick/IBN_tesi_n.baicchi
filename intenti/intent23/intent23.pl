intent(autonomousTractorIntent, largeFarmOp, 250, tractorFleetService).

propertyExpectation(cp_trac, autonomousTractorIntent, security, _, _, trajectoryPlannerVF).
propertyExpectation(hw_trac, autonomousTractorIntent, totChainHW, lower, hard, 128, gb, _, _).
propertyExpectation(lat_trac, autonomousTractorIntent, latency, lower, soft, 15, ms, gateway, trajectoryPlannerVF).

target(tractorFleetService, [positionReceiverVF, soilAnalyzerVF, trajectoryPlannerVF, collisionManagerVF, agriculturalDbVF]).

vnf(positionReceiverVF, edge, 4).
vnf(soilAnalyzerVF, edge, 15).
vnf(trajectoryPlannerVF, edge, 25).
vnf(collisionManagerVF, cloud, 10).
vnf(agriculturalDbVF, cloud, 8).

vnfXUser(positionReceiverVF, s, (1, 250), 16).
vnfXUser(soilAnalyzerVF, m, (1, 250), 32).
vnfXUser(trajectoryPlannerVF, l, (1, 250), 64).
vnfXUser(collisionManagerVF, m, (1, 250), 24).
vnfXUser(agriculturalDbVF, s, (1, 250), 16).
