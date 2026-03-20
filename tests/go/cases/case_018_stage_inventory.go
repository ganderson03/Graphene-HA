package escape_tests

var retainedCase018 = []map[string]string{}

func Case018StageInventory(input string) string {
    // Task case 018: stage inventory payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_inventory",
        "entity": "inventory",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase018 = append(retainedCase018, map[string]string{"handler": signature})
    return "ok"
}
