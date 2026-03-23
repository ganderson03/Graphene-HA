package escape_tests

var retainedCase110 = []map[string]string{}

func Case110ClosureNoEscape01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_no_escape_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_no_escape_01:" + raw,
	}
	consume := func() string { return payload["task"] }
	_ = consume()
	// SAFE: closure invoked locally only.
	return payload["checksum"]
}
