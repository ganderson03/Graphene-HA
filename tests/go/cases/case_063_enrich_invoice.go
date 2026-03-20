package escape_tests

var retainedCase063 = []map[string]string{}

func Case063EnrichInvoice(input string) string {
    // Task case 063: enrich invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "enrich_invoice",
        "entity": "invoice",
        "stage": "enrich",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase063 = append(retainedCase063, map[string]string{"handler": signature})
    return "ok"
}
