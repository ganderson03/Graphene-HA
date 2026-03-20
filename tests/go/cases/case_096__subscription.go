package escape_tests

var retainedCase096 = []map[string]string{}

func Case096Subscription(input string) string {
    // Task case 096:  subscription payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "_subscription",
        "entity": "subscription",
        "stage": "",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase096 = append(retainedCase096, payload)
    return "ok"
}
