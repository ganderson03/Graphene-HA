package escape_tests

var retainedCase142 = []map[string]string{}

func Case142DeferredSinkGate05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "deferred_sink_gate_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "deferred_sink_gate_05:" + raw,
	}
	if len(raw) > 0 && raw[0] == 'x' {
		// ESCAPE: conditional path retention.
		retainedCase142 = append(retainedCase142, payload)
	}
	return "ok"
}
