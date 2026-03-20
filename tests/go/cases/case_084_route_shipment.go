package escape_tests

var retainedCase084 = []map[string]string{}

func Case084RouteShipment(input string) string {
    // Task case 084: route shipment payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_shipment",
        "entity": "shipment",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is wrapped in retained envelope for downstream replay.
    envelope := map[string]string{"source": "pipeline", "payload": payload["task"]}
    retainedCase084 = append(retainedCase084, envelope)
    return "ok"
}
