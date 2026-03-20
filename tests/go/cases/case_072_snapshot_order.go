package escape_tests

var retainedCase072 = []map[string]string{}

func Case072SnapshotOrder(input string) string {
    // Task case 072: snapshot order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "snapshot_order",
        "entity": "order",
        "stage": "snapshot",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase072 = append(retainedCase072, payload)
    return "ok"
}
