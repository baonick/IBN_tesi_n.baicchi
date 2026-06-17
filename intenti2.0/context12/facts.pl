intent(docClassificationIntent, corpDocOp, 50000, documentClassificationEngine).

propertyExpectation(affReq, docClassificationIntent, affinity, same, hard, _, _, ocrScannerVF, textExtractorVF).
propertyExpectation(latReq, docClassificationIntent, latency, lower, hard, 50, ms, textExtractorVF, aiClassifierVF).
propertyExpectation(bwReq, docClassificationIntent, bandwidth, higher, soft, 500, mbps, aiClassifierVF, documentRouterVF).

propertyExpectation(secReq, docClassificationIntent, security, _, ocrScannerVF, _).
propertyExpectation(privReq, docClassificationIntent, privacy, _, _, dataRedactorVF).

target(documentClassificationEngine, [ocrScannerVF, textExtractorVF, aiClassifierVF, dataRedactorVF, documentRouterVF]).

vnf(ocrScannerVF, edge, 16).
vnf(textExtractorVF, edge, 12).
vnf(aiClassifierVF, cloud, 32).
vnf(dataRedactorVF, cloud, 16).
vnf(documentRouterVF, cloud, 8).

vnfXUser(ocrScannerVF, m, (1, 50000), 24).
vnfXUser(textExtractorVF, s, (1, 50000), 12).
vnfXUser(aiClassifierVF, l, (1, 50000), 64).s
vnfXUser(dataRedactorVF, m, (1, 50000), 32).
vnfXUser(documentRouterVF, s, (1, 50000), 8).