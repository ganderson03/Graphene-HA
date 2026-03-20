package escape_tests

var retainedCase011 = []map[string]string{}

func Case011PublishProfile(input string) string {
    // Task case 011: publish profile payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_profile",
        "entity": "profile",
        "stage": "publish",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase011 = append(retainedCase011, payload)
    return "ok"
}
