package escape_tests

var retainedCase032 = []map[string]string{}

func Case032ArchiveOrder(input string) string {
    // Task case 032: archive order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "archive_order",
        "entity": "order",
        "stage": "archive",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase032 = append(retainedCase032, payload)
    return "ok"
}
