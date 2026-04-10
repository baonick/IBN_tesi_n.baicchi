intent(remoteEchoIntent, clinicOp, 50, remoteUltrasoundService).

propertyExpectation(cp_echo, remoteEchoIntent, encoding, _, imagingCollectorVF, _).
propertyExpectation(bw_echo, remoteEchoIntent, bandwidth, greater, hard, 500, megabps, gateway, diagnosticServerVF).
propertyExpectation(aff_echo, remoteEchoIntent, affinity, dedicated, soft, _, _, imagingCollectorVF, _).

target(remoteUltrasoundService, [imagingCollectorVF, diagnosticServerVF]).

vnf(imagingCollectorVF, edge, 8).
vnf(diagnosticServerVF, cloud, 24).

vnfXUser(imagingCollectorVF, m, (1, 50), 16).
vnfXUser(diagnosticServerVF, l, (1, 50), 32).
