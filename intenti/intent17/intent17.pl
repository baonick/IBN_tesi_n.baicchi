intent(arWarehouseIntent, logisticsOp, 2000, workerArService).

propertyExpectation(cp_ar, arWarehouseIntent, privacy, _, _, taskManagerVF).
propertyExpectation(lat_ar, arWarehouseIntent, latency, lower, hard, 12, ms, gateway, arRendererVF).
propertyExpectation(aff_ar, arWarehouseIntent, affinity, same, soft, _, _, visionIngressVF, arRendererVF).

target(workerArService, [visionIngressVF, arRendererVF, taskManagerVF, employeeDbVF]).

vnf(visionIngressVF, edge, 6).
vnf(arRendererVF, edge, 35).
vnf(taskManagerVF, cloud, 12).
vnf(employeeDbVF, cloud, 8).

vnfXUser(visionIngressVF, m, (1, 2000), 24).
vnfXUser(arRendererVF, l, (1, 2000), 64).
vnfXUser(taskManagerVF, m, (1, 2000), 24).
vnfXUser(employeeDbVF, s, (1, 2000), 12).
