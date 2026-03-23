package escape_tests

var retainedCase211 = []map[string]string{}

func Case211ShadowedSinkLocal01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "shadowed_sink_local_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "shadowed_sink_local_01:" + raw,
	}
	retainedCase := []map[string]string{}
	retainedCase = append(retainedCase, payload)
	// SAFE: local shadow variable only.
	return payload["checksum"]
}
