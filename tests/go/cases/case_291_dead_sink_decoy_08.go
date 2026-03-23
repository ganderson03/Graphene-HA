package escape_tests

var retainedCase291 = []map[string]string{}

func Case291DeadSinkDecoy08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_08:" + raw,
	}
	if 1 == 0 {
		retainedCase291 = append(retainedCase291, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
