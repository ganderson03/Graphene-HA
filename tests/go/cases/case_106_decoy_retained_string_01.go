package escape_tests

var retainedCase106 = []map[string]string{}

func Case106DecoyRetainedString01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "decoy_retained_string_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "decoy_retained_string_01:" + raw,
	}
	marker := "retainedCase literal only"
	_ = marker + payload["task"]
	// SAFE: no retained sink receives payload object.
	return payload["checksum"]
}
