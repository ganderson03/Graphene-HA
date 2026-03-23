package escape_tests

var retainedCase160 = []map[string]string{}

func Case160ClosureNoEscape06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_no_escape_06",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_no_escape_06:" + raw,
	}
	consume := func() string { return payload["task"] }
	_ = consume()
	// SAFE: closure invoked locally only.
	return payload["checksum"]
}
