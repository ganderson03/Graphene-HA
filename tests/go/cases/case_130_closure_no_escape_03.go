package escape_tests

var retainedCase130 = []map[string]string{}

func Case130ClosureNoEscape03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_no_escape_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_no_escape_03:" + raw,
	}
	consume := func() string { return payload["task"] }
	_ = consume()
	// SAFE: closure invoked locally only.
	return payload["checksum"]
}
