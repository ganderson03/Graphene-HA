package escape_tests

var retainedCase006 = []map[string]string{}

func Case006CacheSubscription(input string) string {
    // Task case 006: cache subscription payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "cache_subscription",
        "entity": "subscription",
        "stage": "cache",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase006 = append(retainedCase006, payload)
    return "ok"
}
