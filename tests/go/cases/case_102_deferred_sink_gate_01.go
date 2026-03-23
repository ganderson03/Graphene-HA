package escape_tests

var retainedCase102 = []map[string]string{}

func Case102DeferredSinkGate01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "deferred_sink_gate_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "deferred_sink_gate_01:" + raw,
	}
	if len(raw) > 0 && raw[0] == 'x' {
		// ESCAPE: conditional path retention.
		retainedCase102 = append(retainedCase102, payload)
	}
	return "ok"
}
