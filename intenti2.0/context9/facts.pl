intent(vodDistributionIntent, vodStreamOp, 80000, vodDistributionService).


propertyExpectation(bwReq, vodDistributionIntent, bandwidth, higher, hard, 10000, mbps, transcoderVF, cachingNodeVF).
propertyExpectation(affReq, vodDistributionIntent, affinity, same, soft, _, _, drmEncryptorVF, transcoderVF).

propertyExpectation(encReq, vodDistributionIntent, encoding, _, drmEncryptorVF, _).
propertyExpectation(decReq, vodDistributionIntent, decoding, _, _, cachingNodeVF).

target(vodDistributionService, [drmEncryptorVF, transcoderVF, cachingNodeVF]).

vnf(drmEncryptorVF, cloud, 16).
vnf(transcoderVF, cloud, 32).
vnf(cachingNodeVF, edge, 12).

vnfXUser(drmEncryptorVF, m, (1, 80000), 24).
vnfXUser(transcoderVF, l, (1, 80000), 64).
vnfXUser(cachingNodeVF, m, (1, 80000), 16).