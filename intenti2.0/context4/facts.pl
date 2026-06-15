intent(gdprComplianceIntent, gdprComplianceOp, 5000, gdprVerificationService).

% Non-Changing Properties (9 parameters)
propertyExpectation(latReq, gdprComplianceIntent, latency, lower, soft, 20, ms, dbScannerVF, anonymizerVF).
propertyExpectation(bwReq, gdprComplianceIntent, bandwidth, higher, hard, 50, mbps, anonymizerVF, reportGeneratorVF).


propertyExpectation(privReq, gdprComplianceIntent, privacy, _, dbScannerVF, _).
propertyExpectation(secReq, gdprComplianceIntent, security, _, _, reportGeneratorVF).

target(gdprVerificationService, [dbScannerVF, anonymizerVF, reportGeneratorVF]).

vnf(dbScannerVF, edge, 16).
vnf(anonymizerVF, cloud, 24).
vnf(reportGeneratorVF, cloud, 8).

vnfXUser(dbScannerVF, m, (1, 5000), 12).
vnfXUser(anonymizerVF, l, (1, 5000), 24).
vnfXUser(reportGeneratorVF, s, (1, 5000), 6).