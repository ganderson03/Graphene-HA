package escape_tests

var retainedCase043 = []map[string]string{}

func Case043NormalizeInvoice(input string) string {
    // Task case 043: normalize invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_invoice",
        "entity": "invoice",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase043 = append(retainedCase043, map[string]string{"handler": signature})
    return "ok"
}
