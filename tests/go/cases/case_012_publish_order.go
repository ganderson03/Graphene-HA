package escape_tests

var retainedCase012 = []map[string]string{}

func Case012PublishOrder(input string) string {
    // Task case 012: publish order payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_order",
        "entity": "order",
        "stage": "publish",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase012 = append(retainedCase012, payload)
    return "ok"
}
