intent(smartCampusIntent, universityOp, 5000, accessControlService).

propertyExpectation(cp_campus, smartCampusIntent, security, _, _, biometricAnalyzerVF).
propertyExpectation(lat_campus, smartCampusIntent, latency, lower, hard, 10, ms, gateway, accessControllerVF).
propertyExpectation(hw_campus, smartCampusIntent, totChainHW, lower, soft, 64, gb, _, _).

target(accessControlService, [accessTerminalVF, biometricAnalyzerVF, accessControllerVF, campusDbVF]).

vnf(accessTerminalVF, edge, 3).
vnf(biometricAnalyzerVF, edge, 15).
vnf(accessControllerVF, edge, 5).
vnf(campusDbVF, cloud, 8).

vnfXUser(accessTerminalVF, s, (1, 5000), 8).
vnfXUser(biometricAnalyzerVF, m, (1, 5000), 32).
vnfXUser(accessControllerVF, s, (1, 5000), 8).
vnfXUser(campusDbVF, s, (1, 5000), 12).
