package escape_tests

var retainedCase076 = []map[string]string{}

func Case076RouteSubscription(input string) string {
    // Task case 076: route subscription payload for downstream business processing.
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
    retainedCase076 = append(retainedCase076, payload)
    return "ok"
}
