package escape_tests

var retainedCase027 = []map[string]string{}

func Case027ArchiveSession(input string) string {
    // Task case 027: archive session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "archive_session",
        "entity": "session",
        "stage": "archive",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase027 = append(retainedCase027, payload)
    return "ok"
}
