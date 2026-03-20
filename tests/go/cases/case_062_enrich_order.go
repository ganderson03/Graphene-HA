package escape_tests

var retainedCase062 = []map[string]string{}

func Case062EnrichOrder(input string) string {
    // Task case 062: enrich order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "enrich_order",
        "entity": "order",
        "stage": "enrich",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase062 = append(retainedCase062, payload)
    return "ok"
}
