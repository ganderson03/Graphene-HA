package escape_tests

var retainedCase231 = []map[string]string{}

func Case231DeadSinkDecoy03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_03:" + raw,
	}
	if 1 == 0 {
		retainedCase231 = append(retainedCase231, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
