package escape_tests

var retainedCase015 = []map[string]string{}

func Case015PublishTicket(input string) string {
    // Task case 015: publish ticket payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "publish_ticket",
        "entity": "ticket",
        "stage": "publish",
        "input": raw,
    }
    // SAFE: payload remains local; only primitive summary string is returned.
    return payload["task"] + ":" + payload["input"]
}
