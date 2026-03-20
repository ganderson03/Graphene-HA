package escape_tests

var retainedCase001 = []map[string]string{}

func Case001CacheProfile(input string) string {
    // Task case 001: cache profile payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "cache_profile",
        "entity": "profile",
        "stage": "cache",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase001 = append(retainedCase001, payload)
    return "ok"
}
