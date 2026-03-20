package escape_tests

var retainedCase008 = []map[string]string{}

func Case008PublishInventory(input string) string {
    // Task case 008: publish inventory payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_inventory",
        "entity": "inventory",
        "stage": "publish",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase008 = append(retainedCase008, map[string]string{"handler": signature})
    return "ok"
}
