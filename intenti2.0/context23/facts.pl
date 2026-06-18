intent(radiologyAIIntent, medDiagnosticOp, 10000, radiologyPipelineService).

propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, lesionAnalyzerVF, metadataExtractorVF).
propertyExpectation(bwReq, radiologyAIIntent, bandwidth, higher, soft, 500, mbps, dicomIngesterVF, lesionAnalyzerVF).

propertyExpectation(compReq, radiologyAIIntent, compression, _, dicomIngesterVF, _).
propertyExpectation(encReq, radiologyAIIntent, encoding, _, _, secureArchiverVF).

target(radiologyPipelineService, [dicomIngesterVF, lesionAnalyzerVF, metadataExtractorVF, secureArchiverVF]).

vnf(dicomIngesterVF, edge, 16).
vnf(lesionAnalyzerVF, cloud, 32).
vnf(metadataExtractorVF, cloud, 12).
vnf(secureArchiverVF, cloud, 24).

vnfXUser(dicomIngesterVF, m, (1, 10000), 32).
vnfXUser(lesionAnalyzerVF, l, (1, 10000), 64).
vnfXUser(metadataExtractorVF, m, (1, 10000), 24).
vnfXUser(secureArchiverVF, l, (1, 10000), 48).