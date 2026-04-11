intent(agriWeatherIntent, farmCoopOp, 1500, microClimateService).

propertyExpectation(cp_wea, agriWeatherIntent, logging, cloud, forecastEngineVF, _).
propertyExpectation(hw_wea, agriWeatherIntent, totChainHW, lower, hard, 50, gb, _, _).
propertyExpectation(bw_wea, agriWeatherIntent, bandwidth, greater, soft, 50, megabps, weatherCollectorVF, forecastEngineVF).

target(microClimateService, [weatherCollectorVF, forecastEngineVF]).

vnf(weatherCollectorVF, edge, 4).
vnf(forecastEngineVF, cloud, 20).

vnfXUser(weatherCollectorVF, s, (1, 1500), 12).
vnfXUser(forecastEngineVF, l, (1, 1500), 48).
