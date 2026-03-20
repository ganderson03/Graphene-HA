package escape_tests

var retainedCase003 = []map[string]string{}

func Case003CacheInvoice(input string) string {
    // Task case 003: cache invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "cache_invoice",
        "entity": "invoice",
        "stage": "cache",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase003 = append(retainedCase003, map[string]string{"handler": signature})
    return "ok"
}
