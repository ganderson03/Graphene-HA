package escape_tests

var retainedCase038 = []map[string]string{}

func Case038NormalizeInventory(input string) string {
    // Task case 038: normalize inventory payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_inventory",
        "entity": "inventory",
        "stage": "normalize",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase038 = append(retainedCase038, map[string]string{"handler": signature})
    return "ok"
}
