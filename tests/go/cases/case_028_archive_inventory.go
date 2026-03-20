package escape_tests

var retainedCase028 = []map[string]string{}

func Case028ArchiveInventory(input string) string {
    // Task case 028: archive inventory payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "archive_inventory",
        "entity": "inventory",
        "stage": "archive",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase028 = append(retainedCase028, map[string]string{"handler": signature})
    return "ok"
}
