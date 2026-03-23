package escape_tests

var retainedCase279 = []map[string]string{}

func Case279DeadSinkDecoy07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_07:" + raw,
	}
	if 1 == 0 {
		retainedCase279 = append(retainedCase279, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
