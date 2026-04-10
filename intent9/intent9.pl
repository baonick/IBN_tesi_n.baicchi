intent(elderlyCareIntent, healthOp, 15000, vitalMonitoringService).

propertyExpectation(cp_vital, elderlyCareIntent, caching, _, _, anomalyDetectorVF).
propertyExpectation(lat_vital, elderlyCareIntent, latency, lower, hard, 10, ms, gateway, anomalyDetectorVF).
propertyExpectation(aff_vital, elderlyCareIntent, affinity, same, hard, _, _, vitalsAggregatorVF, anomalyDetectorVF).

target(vitalMonitoringService, [vitalsAggregatorVF, anomalyDetectorVF, patientHistoryDbVF]).

vnf(vitalsAggregatorVF, edge, 4).
vnf(anomalyDetectorVF, edge, 20).
vnf(patientHistoryDbVF, cloud, 12).

vnfXUser(vitalsAggregatorVF, m, (1, 15000), 16).
vnfXUser(anomalyDetectorVF, l, (1, 15000), 48).
vnfXUser(patientHistoryDbVF, m, (1, 15000), 24).
