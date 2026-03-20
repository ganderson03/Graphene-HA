package escape_tests

var retainedCase052 = []map[string]string{}

func Case052ScoreOrder(input string) string {
    // Task case 052: score order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "score_order",
        "entity": "order",
        "stage": "score",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase052 = append(retainedCase052, payload)
    return "ok"
}
