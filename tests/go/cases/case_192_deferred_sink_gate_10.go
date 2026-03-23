package escape_tests

var retainedCase192 = []map[string]string{}

func Case192DeferredSinkGate10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "deferred_sink_gate_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "deferred_sink_gate_10:" + raw,
	}
	if len(raw) > 0 && raw[0] == 'x' {
		// ESCAPE: conditional path retention.
		retainedCase192 = append(retainedCase192, payload)
	}
	return "ok"
}
