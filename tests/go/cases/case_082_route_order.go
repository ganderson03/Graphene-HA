package escape_tests

var retainedCase082 = []map[string]string{}

func Case082RouteOrder(input string) string {
    // Task case 082: route order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_order",
        "entity": "order",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase082 = append(retainedCase082, payload)
    return "ok"
}
