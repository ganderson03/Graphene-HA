package escape_tests

var retainedCase004 = []map[string]string{}

func Case004CacheShipment(input string) string {
    // Task case 004: cache shipment payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "cache_shipment",
        "entity": "shipment",
        "stage": "cache",
        "input": raw,
    }
    // ESCAPE: payload is wrapped in retained envelope for downstream replay.
    envelope := map[string]string{"source": "pipeline", "payload": payload["task"]}
    retainedCase004 = append(retainedCase004, envelope)
    return "ok"
}
