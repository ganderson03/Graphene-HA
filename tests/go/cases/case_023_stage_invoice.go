package escape_tests

var retainedCase023 = []map[string]string{}

func Case023StageInvoice(input string) string {
    // Task case 023: stage invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_invoice",
        "entity": "invoice",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase023 = append(retainedCase023, map[string]string{"handler": signature})
    return "ok"
}
