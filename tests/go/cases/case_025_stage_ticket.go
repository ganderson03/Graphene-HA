package escape_tests

var retainedCase025 = []map[string]string{}

func Case025StageTicket(input string) string {
    // Task case 025: stage ticket payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_ticket",
        "entity": "ticket",
        "stage": "stage",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
