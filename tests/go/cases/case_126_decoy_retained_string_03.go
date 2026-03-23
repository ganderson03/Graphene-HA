package escape_tests

var retainedCase126 = []map[string]string{}

func Case126DecoyRetainedString03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "decoy_retained_string_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "decoy_retained_string_03:" + raw,
	}
	marker := "retainedCase literal only"
	_ = marker + payload["task"]
	// SAFE: no retained sink receives payload object.
	return payload["checksum"]
}
