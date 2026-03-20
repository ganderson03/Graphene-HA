package escape_tests

var retainedCase077 = []map[string]string{}

func Case077RouteSession(input string) string {
    // Task case 077: route session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_session",
        "entity": "session",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase077 = append(retainedCase077, payload)
    return "ok"
}
