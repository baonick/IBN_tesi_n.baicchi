intent(vrGamingIntent, gamingCorpOp, 80000, mmoVrService).

propertyExpectation(cp_vr, vrGamingIntent, decoding, _, _, physicsEngineVF).
propertyExpectation(aff_vr, vrGamingIntent, affinity, same, hard, _, _, inputCollectorVF, physicsEngineVF).
propertyExpectation(av_vr, vrGamingIntent, chainAvailability, greater, soft, 0.9999, _, _, _).

target(mmoVrService, [inputCollectorVF, physicsEngineVF, stateServerVF]).

vnf(inputCollectorVF, edge, 5).
vnf(physicsEngineVF, edge, 40).
vnf(stateServerVF, cloud, 15).

vnfXUser(inputCollectorVF, m, (1, 80000), 32).
vnfXUser(physicsEngineVF, l, (1, 80000), 128).
vnfXUser(stateServerVF, l, (1, 80000), 64).
