package escape_tests

var retainedCase098 = []map[string]string{}

func Case098Inventory(input string) string {
    // Task case 098:  inventory payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "_inventory",
        "entity": "inventory",
        "stage": "",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase098 = append(retainedCase098, map[string]string{"handler": signature})
    return "ok"
}
