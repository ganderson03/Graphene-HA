package escape_tests

var retainedCase022 = []map[string]string{}

func Case022StageOrder(input string) string {
    // Task case 022: stage order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_order",
        "entity": "order",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase022 = append(retainedCase022, payload)
    return "ok"
}
