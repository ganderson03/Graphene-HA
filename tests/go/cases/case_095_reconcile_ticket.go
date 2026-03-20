package escape_tests

var retainedCase095 = []map[string]string{}

func Case095ReconcileTicket(input string) string {
    // Task case 095: reconcile ticket payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "reconcile_ticket",
        "entity": "ticket",
        "stage": "reconcile",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
