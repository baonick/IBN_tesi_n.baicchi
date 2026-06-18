intent(eVotingIntent, secureVoteOp, 200000, certifiedVotingService).

propertyExpectation(bwReq, eVotingIntent, bandwidth, higher, soft, 100, mbps, ballotIngesterVF, anonymizerVF).

propertyExpectation(privReq, eVotingIntent, privacy, _, anonymizerVF, _).
propertyExpectation(secReq, eVotingIntent, security, _, _, integrityEnforcerVF).
propertyExpectation(logReq, eVotingIntent, logging, _, _, auditLoggerVF).

target(certifiedVotingService, [ballotIngesterVF, anonymizerVF, integrityEnforcerVF, voteCounterVF, auditLoggerVF]).

vnf(ballotIngesterVF, edge, 12).
vnf(anonymizerVF, cloud, 16).
vnf(integrityEnforcerVF, cloud, 24).
vnf(voteCounterVF, cloud, 16).
vnf(auditLoggerVF, cloud, 12).

vnfXUser(ballotIngesterVF, m, (1, 200000), 24).
vnfXUser(anonymizerVF, m, (1, 200000), 32).
vnfXUser(integrityEnforcerVF, l, (1, 200000), 48).
vnfXUser(voteCounterVF, m, (1, 200000), 32).
vnfXUser(auditLoggerVF, s, (1, 200000), 24).