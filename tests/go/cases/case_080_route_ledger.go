package escape_tests

var retainedCase080 = []map[string]string{}

func Case080RouteLedger(input string) string {
    // Task case 080: route ledger payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_ledger",
        "entity": "ledger",
        "stage": "route",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
