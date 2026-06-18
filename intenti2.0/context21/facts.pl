intent(autonomousWarehouseIntent, autoWarehouseOp, 500, autonomousControlService).

propertyExpectation(latReq, autonomousWarehouseIntent, latency, lower, hard, 20, ms, sensorDataDecoderVF, commandEncoderVF).

propertyExpectation(decReq, autonomousWarehouseIntent, decoding, _, sensorDataDecoderVF, _).
propertyExpectation(encReq, autonomousWarehouseIntent, encoding, _, _, commandEncoderVF).

target(autonomousControlService, [sensorDataDecoderVF, collisionPathSolverVF, commandEncoderVF]).

vnf(sensorDataDecoderVF, edge, 16).
vnf(collisionPathSolverVF, cloud, 32).
vnf(commandEncoderVF, edge, 16).

vnfXUser(sensorDataDecoderVF, m, (1, 500), 32).
vnfXUser(collisionPathSolverVF, l, (1, 500), 64).
vnfXUser(commandEncoderVF, m, (1, 500), 32).