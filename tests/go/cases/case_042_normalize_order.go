package escape_tests

var retainedCase042 = []map[string]string{}

func Case042NormalizeOrder(input string) string {
    // Task case 042: normalize order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_order",
        "entity": "order",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase042 = append(retainedCase042, payload)
    return "ok"
}
