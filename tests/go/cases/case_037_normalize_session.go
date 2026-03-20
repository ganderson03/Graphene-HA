package escape_tests

var retainedCase037 = []map[string]string{}

func Case037NormalizeSession(input string) string {
    // Task case 037: normalize session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_session",
        "entity": "session",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase037 = append(retainedCase037, payload)
    return "ok"
}
