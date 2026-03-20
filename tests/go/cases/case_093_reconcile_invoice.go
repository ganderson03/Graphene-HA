package escape_tests

var retainedCase093 = []map[string]string{}

func Case093ReconcileInvoice(input string) string {
    // Task case 093: reconcile invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "reconcile_invoice",
        "entity": "invoice",
        "stage": "reconcile",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase093 = append(retainedCase093, map[string]string{"handler": signature})
    return "ok"
}
