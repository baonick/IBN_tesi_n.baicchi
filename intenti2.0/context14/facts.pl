intent(hftIntent, hftGlobalOp, 500000, highFrequencyTradingService).

propertyExpectation(latReq1, hftIntent, latency, lower, hard, 2, ms, marketFeedVF, tradingAlgoVF).
propertyExpectation(bwReq, hftIntent, bandwidth, higher, soft, 5000, mbps, tradingAlgoVF, riskCheckerVF).
propertyExpectation(latReq2, hftIntent, latency, lower, soft, 5, ms, riskCheckerVF, orderDispatcherVF).

propertyExpectation(cachReq, hftIntent, caching, _, marketFeedVF, _).
propertyExpectation(logReq, hftIntent, logging, _, _, orderDispatcherVF).

target(highFrequencyTradingService, [marketFeedVF, tradingAlgoVF, riskCheckerVF, orderDispatcherVF]).

vnf(marketFeedVF, edge, 16).
vnf(tradingAlgoVF, edge, 32).
vnf(riskCheckerVF, cloud, 16).
vnf(orderDispatcherVF, edge, 8).

vnfXUser(marketFeedVF, m, (1, 500000), 32).
vnfXUser(tradingAlgoVF, l, (1, 500000), 64).
vnfXUser(riskCheckerVF, m, (1, 500000), 32).
vnfXUser(orderDispatcherVF, s, (1, 500000), 16).