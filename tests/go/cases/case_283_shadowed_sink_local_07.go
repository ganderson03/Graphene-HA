package escape_tests

var retainedCase283 = []map[string]string{}

func Case283ShadowedSinkLocal07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "shadowed_sink_local_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "shadowed_sink_local_07:" + raw,
	}
	retainedCase := []map[string]string{}
	retainedCase = append(retainedCase, payload)
	// SAFE: local shadow variable only.
	return payload["checksum"]
}
