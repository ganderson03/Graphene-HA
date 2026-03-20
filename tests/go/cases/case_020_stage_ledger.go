package escape_tests

var retainedCase020 = []map[string]string{}

func Case020StageLedger(input string) string {
    // Task case 020: stage ledger payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_ledger",
        "entity": "ledger",
        "stage": "stage",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
