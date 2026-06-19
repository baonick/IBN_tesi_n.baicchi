intent(eVotingIntent, secureVoteOp, 200000, certifiedVotingService).

propertyExpectation(bwReq, eVotingIntent, bandwidth, greater, soft, 100, megabps, ballotIngesterVF, anonymizerVF).

propertyExpectation(privReq, eVotingIntent, privacy, _, anonymizerVF, _).
propertyExpectation(secReq, eVotingIntent, security, _, _, integrityEnforcerVF).
propertyExpectation(logReq, eVotingIntent, logging, _, _, auditLoggerVF).

target(certifiedVotingService, [ballotIngesterVF, anonymizerVF, integrityEnforcerVF, voteCounterVF, auditLoggerVF]).

vnf(ballotIngesterVF, edge, 12).
vnf(anonymizerVF, cloud, 16).
vnf(integrityEnforcerVF, cloud, 24).
vnf(voteCounterVF, cloud, 16).
vnf(auditLoggerVF, cloud, 12).

vnfXUser(ballotIngesterVF, l, (1, 200000), 12).
vnfXUser(anonymizerVF, l, (1, 200000), 16).
vnfXUser(integrityEnforcerVF, l, (1, 200000), 24).
vnfXUser(voteCounterVF, l, (1, 200000), 16).
vnfXUser(auditLoggerVF, l, (1, 200000), 12).