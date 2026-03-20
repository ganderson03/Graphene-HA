package escape_tests

var retainedCase047 = []map[string]string{}

func Case047ScoreSession(input string) string {
    // Task case 047: score session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "score_session",
        "entity": "session",
        "stage": "score",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase047 = append(retainedCase047, payload)
    return "ok"
}
