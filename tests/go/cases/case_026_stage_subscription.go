package escape_tests

var retainedCase026 = []map[string]string{}

func Case026StageSubscription(input string) string {
    // Task case 026: stage subscription payload for downstream business processing.
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
    retainedCase026 = append(retainedCase026, payload)
    return "ok"
}
