package escape_tests

var retainedCase081 = []map[string]string{}

func Case081RouteProfile(input string) string {
    // Task case 081: route profile payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_profile",
        "entity": "profile",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase081 = append(retainedCase081, payload)
    return "ok"
}
