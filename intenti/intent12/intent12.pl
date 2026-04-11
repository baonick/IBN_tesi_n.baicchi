intent(factoryQAIntent, manufacturingOp, 200, visionInspectionService).

propertyExpectation(cp_qa, factoryQAIntent, security, _, _, defectDetectorVF).
propertyExpectation(lat_qa, factoryQAIntent, latency, lower, hard, 5, ms, gateway, defectDetectorVF).
propertyExpectation(av_qa, factoryQAIntent, chainAvailability, greater, hard, 0.99999, _, _, _).

target(visionInspectionService, [visionIngressVF, preProcessorVF, defectDetectorVF, alertManagerVF, qualityArchiveVF]).

vnf(visionIngressVF, edge, 4).
vnf(preProcessorVF, edge, 10).
vnf(defectDetectorVF, edge, 25).
vnf(alertManagerVF, cloud, 5).
vnf(qualityArchiveVF, cloud, 10).

vnfXUser(visionIngressVF, s, (1, 200), 8).
vnfXUser(preProcessorVF, m, (1, 200), 16).
vnfXUser(defectDetectorVF, l, (1, 200), 48).
vnfXUser(alertManagerVF, s, (1, 200), 4).
vnfXUser(qualityArchiveVF, m, (1, 200), 16).
