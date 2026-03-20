package escape_tests

var retainedCase013 = []map[string]string{}

func Case013PublishInvoice(input string) string {
    // Task case 013: publish invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_invoice",
        "entity": "invoice",
        "stage": "publish",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase013 = append(retainedCase013, map[string]string{"handler": signature})
    return "ok"
}
