intent(teleMonitoringIntent, healthCareOp, 5000, postOperativeTeleMonitoringService).

propertyExpectation(latReq, teleMonitoringIntent, latency, lower, hard, 100, ms, begin, end).
propertyExpectation(hwReq, teleMonitoringIntent, totChainHW, lower, soft, 80, gb, _, _).

propertyExpectation(privReq, teleMonitoringIntent, privacy, _, patientDataReceiverVF, _).
propertyExpectation(logReq, teleMonitoringIntent, logging, _, _, medicalAlertLoggerVF).

target(postOperativeTeleMonitoringService, [patientDataReceiverVF, cardiacAnomalyAnalyzerVF, medicalAlertLoggerVF, doctorNotifierVF]).

vnf(patientDataReceiverVF, edge, 8).
vnf(cardiacAnomalyAnalyzerVF, cloud, 24).
vnf(medicalAlertLoggerVF, cloud, 12).
vnf(doctorNotifierVF, cloud, 8).

vnfXUser(patientDataReceiverVF, m, (1, 5000), 16).
vnfXUser(cardiacAnomalyAnalyzerVF, l, (1, 5000), 48).
vnfXUser(medicalAlertLoggerVF, m, (1, 5000), 24).
vnfXUser(doctorNotifierVF, s, (1, 5000), 16).