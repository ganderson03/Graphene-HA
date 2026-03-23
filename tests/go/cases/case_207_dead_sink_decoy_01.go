package escape_tests

var retainedCase207 = []map[string]string{}

func Case207DeadSinkDecoy01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_sink_decoy_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "dead_sink_decoy_01:" + raw,
	}
	if 1 == 0 {
		retainedCase207 = append(retainedCase207, payload)
	}
	// SAFE: dead branch never executes sink.
	return payload["checksum"]
}
