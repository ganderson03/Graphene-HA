package escape_tests

var retainedCase002 = []map[string]string{}

func Case002CacheOrder(input string) string {
    // Task case 002: cache order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "cache_order",
        "entity": "order",
        "stage": "cache",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase002 = append(retainedCase002, payload)
    return "ok"
}
