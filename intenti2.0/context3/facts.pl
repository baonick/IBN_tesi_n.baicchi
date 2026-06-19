intent(antiDdosIntent, ddosProtectionOp, 50000, ddosMitigationService).

propertyExpectation(bwReq, antiDdosIntent, bandwidth, greater, hard, 500, megabps, trafficAnalyzerVF, scrubbingFilterVF).
propertyExpectation(latReq, antiDdosIntent, latency, lower, soft, 10, ms, rateLimiterVF, webServerVF).

propertyExpectation(secReq, antiDdosIntent, security, _, _, scrubbingFilterVF).
propertyExpectation(logReq, antiDdosIntent, logging, _, rateLimiterVF, _).

target(ddosMitigationService, [trafficAnalyzerVF, scrubbingFilterVF, rateLimiterVF, webServerVF]).

vnf(trafficAnalyzerVF, edge, 8).
vnf(scrubbingFilterVF, cloud, 32).
vnf(rateLimiterVF, cloud, 16).
vnf(webServerVF, cloud, 12).

vnfXUser(trafficAnalyzerVF, l, (1, inf), 8).
vnfXUser(scrubbingFilterVF, l, (1, inf), 32).
vnfXUser(rateLimiterVF, l, (1, inf), 16).
vnfXUser(webServerVF, l, (1, inf), 12).