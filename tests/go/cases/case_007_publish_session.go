package escape_tests

var retainedCase007 = []map[string]string{}

func Case007PublishSession(input string) string {
    // Task case 007: publish session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_session",
        "entity": "session",
        "stage": "publish",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase007 = append(retainedCase007, payload)
    return "ok"
}
