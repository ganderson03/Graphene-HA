package escape_tests

var retainedCase053 = []map[string]string{}

func Case053ScoreInvoice(input string) string {
    // Task case 053: score invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "score_invoice",
        "entity": "invoice",
        "stage": "score",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase053 = append(retainedCase053, map[string]string{"handler": signature})
    return "ok"
}
