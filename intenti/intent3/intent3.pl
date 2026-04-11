intent(vrEduIntent, universityOp, 3000, vrClassroomService).

propertyExpectation(cp_edu, vrEduIntent, decoding, _, _, classroomServerVF).
propertyExpectation(bw_edu, vrEduIntent, bandwidth, greater, hard, 1000, megabps, gateway, classroomServerVF).
propertyExpectation(aff_edu, vrEduIntent, affinity, same, hard, _, _, mediaIngressVF, classroomServerVF).

target(vrClassroomService, [mediaIngressVF, classroomServerVF, studentDbVF]).

vnf(mediaIngressVF, edge, 6).
vnf(classroomServerVF, edge, 30).
vnf(studentDbVF, cloud, 5).

vnfXUser(mediaIngressVF, m, (1, 3000), 24).
vnfXUser(classroomServerVF, l, (1, 3000), 64).
vnfXUser(studentDbVF, s, (1, 3000), 12).
