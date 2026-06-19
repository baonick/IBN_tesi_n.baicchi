intent(arBackendIntent, factoryCloudOp, 500, arRenderingService).

propertyExpectation(latReq, arBackendIntent, latency, lower, hard, 12, ms, begin, end).
propertyExpectation(bwReq, arBackendIntent, bandwidth, higher, soft, 200, mbps, arStreamReceiverVF, arPoseEstimatorVF).
propertyExpectation(hwReq, arBackendIntent, totChainHW, lower, soft, 90, gb, _, _).
propertyExpectation(affReq, arBackendIntent, affinity, dedicated, hard, _, _, arPoseEstimatorVF, dataOverlayEngineVF).

target(arRenderingService, [arStreamReceiverVF, arPoseEstimatorVF, dataOverlayEngineVF, arStreamDispatcherVF]).

vnf(arStreamReceiverVF, edge, 12).
vnf(arPoseEstimatorVF, cloud, 24).
vnf(dataOverlayEngineVF, cloud, 32).
vnf(arStreamDispatcherVF, cloud, 16).

vnfXUser(arStreamReceiverVF, m, (1, 500), 12).
vnfXUser(arPoseEstimatorVF, l, (1, 500), 24).
vnfXUser(dataOverlayEngineVF, l, (1, 500), 32).
vnfXUser(arStreamDispatcherVF, m, (1, 500), 16).