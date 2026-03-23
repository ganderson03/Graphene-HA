package escape_tests

var retainedCase243 = []map[string]string{}

func Case243DeadSinkDecoy04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_04",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_04:" + raw,
	}
	if 1 == 0 {
		retainedCase243 = append(retainedCase243, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
