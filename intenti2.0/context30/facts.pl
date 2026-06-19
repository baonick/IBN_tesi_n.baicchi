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

vnfXUser(codeReceiverVF, l, (1, 20000), 8).
vnfXUser(syntaxValidatorVF, l, (1, 20000), 12).
vnfXUser(sandboxSimulatorVF, l, (1, 20000), 32).
vnfXUser(optimizationEngineVF, l, (1, 20000), 24).
vnfXUser(reportGeneratorVF, l, (1, 20000), 16).