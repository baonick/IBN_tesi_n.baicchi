intent(arMaintenanceIntent, manufacturingOp, 150, remoteMaintenanceService).

propertyExpectation(cp_maint, arMaintenanceIntent, encoding, _, visionIngressVF, _).
propertyExpectation(bw_maint, arMaintenanceIntent, bandwidth, greater, hard, 500, megabps, gateway, arServerVF).
propertyExpectation(lat_maint, arMaintenanceIntent, latency, lower, soft, 15, ms, gateway, arServerVF).

target(remoteMaintenanceService, [visionIngressVF, arServerVF, maintenanceDbVF]).

vnf(visionIngressVF, edge, 5).
vnf(arServerVF, edge, 25).
vnf(maintenanceDbVF, cloud, 6).

vnfXUser(visionIngressVF, s, (1, 150), 16).
vnfXUser(arServerVF, l, (1, 150), 64).
vnfXUser(maintenanceDbVF, s, (1, 150), 8).