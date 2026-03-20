package escape_tests

var retainedCase041 = []map[string]string{}

func Case041NormalizeProfile(input string) string {
    // Task case 041: normalize profile payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_profile",
        "entity": "profile",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase041 = append(retainedCase041, payload)
    return "ok"
}
