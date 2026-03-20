package escape_tests

var retainedCase078 = []map[string]string{}

func Case078RouteInventory(input string) string {
    // Task case 078: route inventory payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_inventory",
        "entity": "inventory",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase078 = append(retainedCase078, map[string]string{"handler": signature})
    return "ok"
}
