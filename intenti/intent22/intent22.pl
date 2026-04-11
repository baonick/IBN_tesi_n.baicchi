intent(remoteSurgeryIntent, hospitalConsortiumOp, 100, roboticSurgeryService).

propertyExpectation(cp_surg, remoteSurgeryIntent, decoding, _, _, signalProcessorVF).
propertyExpectation(av_surg, remoteSurgeryIntent, chainAvailability, greater, hard, 0.80, _, _, _).
propertyExpectation(bw_surg, remoteSurgeryIntent, bandwidth, greater, hard, 1500, megabps, commandCollectorVF, signalProcessorVF).

target(roboticSurgeryService, [commandCollectorVF, signalProcessorVF, surgicalServerVF, clinicalArchiveVF]).

vnf(commandCollectorVF, edge, 8).
vnf(signalProcessorVF, edge, 20).
vnf(surgicalServerVF, edge, 45).
vnf(clinicalArchiveVF, cloud, 15).

vnfXUser(commandCollectorVF, m, (1, 100), 32).
vnfXUser(signalProcessorVF, l, (1, 100), 64).
vnfXUser(surgicalServerVF, l, (1, 100), 128).
vnfXUser(clinicalArchiveVF, m, (1, 100), 48).
