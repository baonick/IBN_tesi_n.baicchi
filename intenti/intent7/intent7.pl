intent(cctvIntent, policeDeptOp, 5000, citySurveillanceService).

propertyExpectation(cp_cctv, cctvIntent, privacy, _, _, threatDetectorVF).
propertyExpectation(aff_cctv, cctvIntent, affinity, dedicated, hard, _, _, threatDetectorVF, _).
propertyExpectation(hw_cctv, cctvIntent, totChainHW, lower, soft, 128, gb, _, _).

target(citySurveillanceService, [videoCollectorVF, threatDetectorVF, recordArchiveVF]).

vnf(videoCollectorVF, edge, 8).
vnf(threatDetectorVF, edge, 30).
vnf(recordArchiveVF, cloud, 20).

vnfXUser(videoCollectorVF, m, (1, 5000), 24).
vnfXUser(threatDetectorVF, l, (1, 5000), 64).
vnfXUser(recordArchiveVF, l, (1, 5000), 48).
