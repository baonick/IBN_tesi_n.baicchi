intent(secureMailIntent, secureMailOp, 10000, emailSanitizationService).


propertyExpectation(latReq, secureMailIntent, latency, lower, soft, 50, ms, mailGatewayVF, phishingFilterVF).
propertyExpectation(bwReq, secureMailIntent, bandwidth, higher, hard, 100, mbps, phishingFilterVF, sandboxScannerVF).


propertyExpectation(decReq, secureMailIntent, decoding, _, mailGatewayVF, _).
propertyExpectation(logReq, secureMailIntent, logging, _, _, sandboxScannerVF).

target(emailSanitizationService, [mailGatewayVF, phishingFilterVF, sandboxScannerVF, safeDeliveryVF]).

vnf(mailGatewayVF, edge, 4).
vnf(phishingFilterVF, cloud, 8).
vnf(sandboxScannerVF, cloud, 16).
vnf(safeDeliveryVF, cloud, 4).

vnfXUser(mailGatewayVF, m, (1, 10000), 8).
vnfXUser(phishingFilterVF, m, (1, 10000), 16).
vnfXUser(sandboxScannerVF, l, (1, 10000), 32).
vnfXUser(safeDeliveryVF, s, (1, 10000), 4).