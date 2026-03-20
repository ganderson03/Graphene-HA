package escape_tests

var retainedCase100 = []map[string]string{}

func Case100Ledger(input string) string {
    // Task case 100:  ledger payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "_ledger",
        "entity": "ledger",
        "stage": "",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
