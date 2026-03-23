package escape_tests

var retainedCase255 = []map[string]string{}

func Case255DeadSinkDecoy05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_05:" + raw,
	}
	if 1 == 0 {
		retainedCase255 = append(retainedCase255, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
