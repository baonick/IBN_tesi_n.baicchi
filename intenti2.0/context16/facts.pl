intent(eInvoiceIntent, eInvoiceOp, 50000, electronicInvoicingService).

propertyExpectation(hwReq, eInvoiceIntent, totChainHW, lower, hard, 150, gb, _, _).
propertyExpectation(latReq, eInvoiceIntent, latency, lower, hard, 20, ms, xmlConverterVF, digitalSignerVF).
propertyExpectation(bwReq, eInvoiceIntent, bandwidth, higher, soft, 100, mbps, digitalSignerVF, taxAuthorityTransmitterVF).


target(electronicInvoicingService, [saleDataCollectorVF, xmlConverterVF, digitalSignerVF, taxAuthorityTransmitterVF]).

vnf(saleDataCollectorVF, edge, 8).
vnf(xmlConverterVF, cloud, 16).
vnf(digitalSignerVF, cloud, 12).
vnf(taxAuthorityTransmitterVF, cloud, 8).

vnfXUser(saleDataCollectorVF, s, (1, 50000), 16).
vnfXUser(xmlConverterVF, m, (1, 50000), 32).
vnfXUser(digitalSignerVF, m, (1, 50000), 24).
vnfXUser(taxAuthorityTransmitterVF, s, (1, 50000), 16).