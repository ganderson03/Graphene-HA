package escape_tests

var retainedCase024 = []map[string]string{}

func Case024StageShipment(input string) string {
    // Task case 024: stage shipment payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_shipment",
        "entity": "shipment",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is wrapped in retained envelope for downstream replay.
    envelope := map[string]string{"source": "pipeline", "payload": payload["task"]}
    retainedCase024 = append(retainedCase024, envelope)
    return "ok"
}
