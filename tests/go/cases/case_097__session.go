package escape_tests

var retainedCase097 = []map[string]string{}

func Case097Session(input string) string {
    // Task case 097:  session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "_session",
        "entity": "session",
        "stage": "",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase097 = append(retainedCase097, payload)
    return "ok"
}
