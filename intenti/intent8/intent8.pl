intent(windFarmIntent, energyOp, 600, offshoreWindService).

propertyExpectation(cp_wind, windFarmIntent, security, _, _, structuralAnalyzerVF).
propertyExpectation(av_wind, windFarmIntent, chainAvailability, greater, hard, 0.9999, _, _, _).
propertyExpectation(bw_wind, windFarmIntent, bandwidth, greater, soft, 200, megabps, gateway, structuralAnalyzerVF).

target(offshoreWindService, [turbineReceiverVF, structuralAnalyzerVF, maintenanceRegistryVF]).

vnf(turbineReceiverVF, edge, 3).
vnf(structuralAnalyzerVF, edge, 15).
vnf(maintenanceRegistryVF, cloud, 8).

vnfXUser(turbineReceiverVF, s, (1, 600), 8).
vnfXUser(structuralAnalyzerVF, m, (1, 600), 24).
vnfXUser(maintenanceRegistryVF, m, (1, 600), 16).
