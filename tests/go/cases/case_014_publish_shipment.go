package escape_tests

var retainedCase014 = []map[string]string{}

func Case014PublishShipment(input string) string {
    // Task case 014: publish shipment payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_shipment",
        "entity": "shipment",
        "stage": "publish",
        "input": raw,
    }
    // ESCAPE: payload is wrapped in retained envelope for downstream replay.
    envelope := map[string]string{"source": "pipeline", "payload": payload["task"]}
    retainedCase014 = append(retainedCase014, envelope)
    return "ok"
}
