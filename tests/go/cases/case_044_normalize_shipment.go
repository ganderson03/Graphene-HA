package escape_tests

var retainedCase044 = []map[string]string{}

func Case044NormalizeShipment(input string) string {
    // Task case 044: normalize shipment payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_shipment",
        "entity": "shipment",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is wrapped in retained envelope for downstream replay.
    envelope := map[string]string{"source": "pipeline", "payload": payload["task"]}
    retainedCase044 = append(retainedCase044, envelope)
    return "ok"
}
