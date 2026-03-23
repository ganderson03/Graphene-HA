package escape_tests

var retainedCase295 = []map[string]string{}

func Case295ShadowedSinkLocal08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "shadowed_sink_local_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "shadowed_sink_local_08:" + raw,
	}
	retainedCase := []map[string]string{}
	retainedCase = append(retainedCase, payload)
	// SAFE: local shadow variable only.
	return payload["checksum"]
}
