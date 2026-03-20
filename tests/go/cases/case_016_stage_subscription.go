package escape_tests

var retainedCase016 = []map[string]string{}

func Case016StageSubscription(input string) string {
    // Task case 016: stage subscription payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_subscription",
        "entity": "subscription",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase016 = append(retainedCase016, payload)
    return "ok"
}
