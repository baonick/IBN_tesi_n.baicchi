
intent(smartWasteIntent, municipalityOp, 15000, wasteCollectionService).

propertyExpectation(cp_waste, smartWasteIntent, caching, _, _, collectionOptimizerVF).
propertyExpectation(lat_waste, smartWasteIntent, latency, lower, hard, 20, ms, gateway, collectionOptimizerVF).
propertyExpectation(aff_waste, smartWasteIntent, affinity, same, soft, _, _, volumetricReceiverVF, collectionOptimizerVF).

target(wasteCollectionService, [volumetricReceiverVF, collectionOptimizerVF, operationalLogVF]).

vnf(volumetricReceiverVF, edge, 3).
vnf(collectionOptimizerVF, edge, 15).
vnf(operationalLogVF, cloud, 8).

vnfXUser(volumetricReceiverVF, s, (1, 15000), 12).
vnfXUser(collectionOptimizerVF, m, (1, 15000), 32).
vnfXUser(operationalLogVF, s, (1, 15000), 16).
