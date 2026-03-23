package escape_tests

var retainedCase267 = []map[string]string{}

func Case267DeadSinkDecoy06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_06",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_06:" + raw,
	}
	if 1 == 0 {
		retainedCase267 = append(retainedCase267, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
