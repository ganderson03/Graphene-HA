package escape_tests

var retainedCase186 = []map[string]string{}

func Case186DecoyRetainedString09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "decoy_retained_string_09",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "decoy_retained_string_09:" + raw,
	}
	marker := "retainedCase literal only"
	_ = marker + payload["task"]
	// SAFE: no retained sink receives payload object.
	return payload["checksum"]
}
