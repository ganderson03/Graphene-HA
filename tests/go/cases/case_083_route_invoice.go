package escape_tests

var retainedCase083 = []map[string]string{}

func Case083RouteInvoice(input string) string {
    // Task case 083: route invoice payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "route_invoice",
        "entity": "invoice",
        "stage": "route",
        "input": raw,
    }
    // ESCAPE: payload is captured by retained closure metadata.
    signature := payload["task"] + ":" + payload["input"]
    retainedCase083 = append(retainedCase083, map[string]string{"handler": signature})
    return "ok"
}
