intent(fraudDetectionIntent, fraudSafeOp, 200000, fraudDetectionService).


propertyExpectation(affReq, fraudDetectionIntent, affinity, same, hard, _, _, requestInterceptorVF, profileMatcherVF).
propertyExpectation(bwReq, fraudDetectionIntent, bandwidth, higher, soft, 1000, mbps, mlAnalyzerVF, policyEnforcerVF).
propertyExpectation(hwReq, fraudDetectionIntent, totChainHW, lower, soft, 120, gb, _, _).

propertyExpectation(secReq, fraudDetectionIntent, security, _, requestInterceptorVF, _).
propertyExpectation(privReq, fraudDetectionIntent, privacy, _, _, mlAnalyzerVF).

target(fraudDetectionService, [requestInterceptorVF, profileMatcherVF, mlAnalyzerVF, policyEnforcerVF, responseEmitterVF]).

vnf(requestInterceptorVF, edge, 8).
vnf(profileMatcherVF, edge, 16).
vnf(mlAnalyzerVF, cloud, 32).
vnf(policyEnforcerVF, cloud, 12).
vnf(responseEmitterVF, cloud, 8).

vnfXUser(requestInterceptorVF, s, (1, 200000), 16).
vnfXUser(profileMatcherVF, m, (1, 200000), 32).
vnfXUser(mlAnalyzerVF, l, (1, 200000), 64).
vnfXUser(policyEnforcerVF, m, (1, 200000), 24).
vnfXUser(responseEmitterVF, s, (1, 200000), 16).