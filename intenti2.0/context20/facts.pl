intent(telemetryMonitorIntent, serverMonOp, 50000, telemetryMonitoringService).

propertyExpectation(affReq, telemetryMonitorIntent, affinity, same, hard, _, _, telemetryCollectorVF, dataAggregatorVF).
propertyExpectation(latReq, telemetryMonitorIntent, latency, lower, hard, 100, ms, begin, end).
propertyExpectation(bwReq, telemetryMonitorIntent, bandwidth, higher, soft, 2000, mbps, begin, end).

target(telemetryMonitoringService, [telemetryCollectorVF, dataAggregatorVF, anomalyDetectorVF, alertDispatcherVF]).

vnf(telemetryCollectorVF, edge, 8).
vnf(dataAggregatorVF, cloud, 16).
vnf(anomalyDetectorVF, cloud, 24).
vnf(alertDispatcherVF, cloud, 8).

vnfXUser(telemetryCollectorVF, s, (1, 50000), 16).
vnfXUser(dataAggregatorVF, m, (1, 50000), 32).
vnfXUser(anomalyDetectorVF, l, (1, 50000), 48).
vnfXUser(alertDispatcherVF, s, (1, 50000), 16).