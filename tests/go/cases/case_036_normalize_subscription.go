package escape_tests

var retainedCase036 = []map[string]string{}

func Case036NormalizeSubscription(input string) string {
    // Task case 036: normalize subscription payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_subscription",
        "entity": "subscription",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase036 = append(retainedCase036, payload)
    return "ok"
}
