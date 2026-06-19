intent(virtualLabIntent, eduCloudOp, 10000, virtualLabService).

propertyExpectation(latReq, virtualLabIntent, latency, lower, hard, 40, ms, sessionIngesterVF, activityMonitorVF).
propertyExpectation(bwReq, virtualLabIntent, bandwidth, higher, soft, 500, mbps, sessionIngesterVF, resourceAllocatorVF).
propertyExpectation(hwReq, virtualLabIntent, totChainHW, lower, soft, 120, gb, _, _).

propertyExpectation(privReq, virtualLabIntent, privacy, _, sessionIngesterVF, _).
propertyExpectation(secReq, virtualLabIntent, security, _, _, activityMonitorVF).
propertyExpectation(logReq, virtualLabIntent, logging, _, _, auditLoggerVF).
propertyExpectation(compReq, virtualLabIntent, compression, _, outputPackagerVF, _).

target(virtualLabService, [sessionIngesterVF, resourceAllocatorVF, activityMonitorVF, userPrivacyEnforcerVF, auditLoggerVF, outputPackagerVF]).

vnf(sessionIngesterVF, edge, 8).
vnf(resourceAllocatorVF, cloud, 16).
vnf(activityMonitorVF, cloud, 24).
vnf(userPrivacyEnforcerVF, cloud, 12).
vnf(auditLoggerVF, cloud, 12).
vnf(outputPackagerVF, cloud, 16).

vnfXUser(sessionIngesterVF, s, (1, 10000), 16).
vnfXUser(resourceAllocatorVF, m, (1, 10000), 32).
vnfXUser(activityMonitorVF, l, (1, 10000), 48).
vnfXUser(userPrivacyEnforcerVF, m, (1, 10000), 24).
vnfXUser(auditLoggerVF, m, (1, 10000), 24).
vnfXUser(outputPackagerVF, m, (1, 10000), 32).