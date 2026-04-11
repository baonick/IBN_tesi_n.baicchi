intent(pipelineLeakIntent, oilCompanyOp, 5000, leakDetectionService).

propertyExpectation(cp_leak, pipelineLeakIntent, compression, _, _, leakAnalyzerVF).
propertyExpectation(lat_leak, pipelineLeakIntent, latency, lower, soft, 40, ms, gateway, leakAnalyzerVF).
propertyExpectation(hw_leak, pipelineLeakIntent, totChainHW, lower, hard, 32, gb, _, _).

target(leakDetectionService, [acousticAggregatorVF, leakAnalyzerVF]).

vnf(acousticAggregatorVF, edge, 4).
vnf(leakAnalyzerVF, cloud, 16).

vnfXUser(acousticAggregatorVF, m, (1, 5000), 12).
vnfXUser(leakAnalyzerVF, m, (1, 5000), 24).
