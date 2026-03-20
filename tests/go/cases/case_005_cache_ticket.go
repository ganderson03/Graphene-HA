package escape_tests

var retainedCase005 = []map[string]string{}

func Case005CacheTicket(input string) string {
    // Task case 005: cache ticket payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "cache_ticket",
        "entity": "ticket",
        "stage": "cache",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
