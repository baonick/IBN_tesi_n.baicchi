intent(multiCamIntent, mediaBroadcastOp, 30000, liveStreamingService).

propertyExpectation(bwReq, multiCamIntent, bandwidth, higher, hard, 5000, mbps, graphicInjectorVF, streamDistributorVF).
propertyExpectation(hwReq, multiCamIntent, totChainHW, lower, soft, 150, gb, _, _).

propertyExpectation(compReq, multiCamIntent, compression, _, streamIngesterVF, _).
propertyExpectation(cachReq, multiCamIntent, caching, _, _, streamDistributorVF).

target(liveStreamingService, [streamIngesterVF, cloudStudioVF, graphicInjectorVF, streamDistributorVF]).

vnf(streamIngesterVF, edge, 12).
vnf(cloudStudioVF, cloud, 32).
vnf(graphicInjectorVF, cloud, 16).
vnf(streamDistributorVF, cloud, 24).

vnfXUser(streamIngesterVF, m, (1, 30000), 24).
vnfXUser(cloudStudioVF, l, (1, 30000), 64).
vnfXUser(graphicInjectorVF, m, (1, 30000), 32).
vnfXUser(streamDistributorVF, l, (1, 30000), 48).