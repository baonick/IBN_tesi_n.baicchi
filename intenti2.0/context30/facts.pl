intent(codeAnalyzerIntent, devToolsOp, 20000, codeOptimizationService).

propertyExpectation(hwReq, codeAnalyzerIntent, totChainHW, lower, soft, 110, gb, _, _).


propertyExpectation(cachReq, codeAnalyzerIntent, caching, _, syntaxValidatorVF, _).
propertyExpectation(compReq, codeAnalyzerIntent, compression, _, reportGeneratorVF, _).

target(codeOptimizationService, [codeReceiverVF, syntaxValidatorVF, sandboxSimulatorVF, optimizationEngineVF, reportGeneratorVF]).

vnf(codeReceiverVF, edge, 8).
vnf(syntaxValidatorVF, cloud, 12).
vnf(sandboxSimulatorVF, cloud, 32).
vnf(optimizationEngineVF, cloud, 24).
vnf(reportGeneratorVF, cloud, 16).

vnfXUser(codeReceiverVF, s, (1, 20000), 16).
vnfXUser(syntaxValidatorVF, m, (1, 20000), 24).
vnfXUser(sandboxSimulatorVF, l, (1, 20000), 64).
vnfXUser(optimizationEngineVF, l, (1, 20000), 48).
vnfXUser(reportGeneratorVF, m, (1, 20000), 32).