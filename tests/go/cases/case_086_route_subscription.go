package escape_tests

var retainedCase086 = []map[string]string{}

func Case086RouteSubscription(input string) string {
    // Task case 086: route subscription payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_subscription",
        "entity": "subscription",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase086 = append(retainedCase086, payload)
    return "ok"
}
