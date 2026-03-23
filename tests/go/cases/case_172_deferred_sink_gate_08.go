package escape_tests

var retainedCase172 = []map[string]string{}

func Case172DeferredSinkGate08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "deferred_sink_gate_08",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "deferred_sink_gate_08:" + raw,
	}
	if len(raw) > 0 && raw[0] == 'x' {
		// ESCAPE: conditional path retention.
		retainedCase172 = append(retainedCase172, payload)
	}
	return "ok"
}
