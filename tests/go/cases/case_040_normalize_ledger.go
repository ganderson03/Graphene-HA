package escape_tests

var retainedCase040 = []map[string]string{}

func Case040NormalizeLedger(input string) string {
    // Task case 040: normalize ledger payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "normalize_ledger",
        "entity": "ledger",
        "stage": "normalize",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
