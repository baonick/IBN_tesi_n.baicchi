intent(govDataIntent, govDataOp, 30000, openDataPortalService).

propertyExpectation(latReq, govDataIntent, latency, lower, hard, 200, ms, begin, end).
propertyExpectation(bwReq, govDataIntent, bandwidth, higher, soft, 1000, mbps, formatNormalizerVF, metadataEnricherVF).
propertyExpectation(affReq, govDataIntent, affinity, same, hard, _, _, formatNormalizerVF, metadataEnricherVF).

propertyExpectation(cachReq, govDataIntent, caching, _, formatNormalizerVF, _).

target(openDataPortalService, [dataExtractorVF, formatNormalizerVF, metadataEnricherVF, downloadProviderVF]).

vnf(dataExtractorVF, edge, 8).
vnf(formatNormalizerVF, cloud, 16).
vnf(metadataEnricherVF, cloud, 12).
vnf(downloadProviderVF, cloud, 16).

vnfXUser(dataExtractorVF, s, (1, 30000), 16).
vnfXUser(formatNormalizerVF, m, (1, 30000), 32).
vnfXUser(metadataEnricherVF, m, (1, 30000), 24).
vnfXUser(downloadProviderVF, m, (1, 30000), 32).