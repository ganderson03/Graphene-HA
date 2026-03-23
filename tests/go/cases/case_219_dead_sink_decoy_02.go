package escape_tests

var retainedCase219 = []map[string]string{}

func Case219DeadSinkDecoy02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_02:" + raw,
	}
	if 1 == 0 {
		retainedCase219 = append(retainedCase219, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
