package escape_tests

var retainedCase122 = []map[string]string{}

func Case122DeferredSinkGate03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "deferred_sink_gate_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "deferred_sink_gate_03:" + raw,
	}
	if len(raw) > 0 && raw[0] == 'x' {
		// ESCAPE: conditional path retention.
		retainedCase122 = append(retainedCase122, payload)
	}
	return "ok"
}
