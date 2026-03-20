package escape_tests

var retainedCase092 = []map[string]string{}

func Case092ReconcileOrder(input string) string {
    // Task case 092: reconcile order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "reconcile_order",
        "entity": "order",
        "stage": "reconcile",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase092 = append(retainedCase092, payload)
    return "ok"
}
