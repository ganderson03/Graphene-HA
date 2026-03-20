package escape_tests

var retainedCase017 = []map[string]string{}

func Case017StageSession(input string) string {
    // Task case 017: stage session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_session",
        "entity": "session",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase017 = append(retainedCase017, payload)
    return "ok"
}
