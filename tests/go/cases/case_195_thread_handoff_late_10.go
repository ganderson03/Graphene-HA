package escape_tests

var retainedCase195 = []map[string]string{}

func Case195ThreadHandoffLate10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_10:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase195 = append(retainedCase195, p)
	}(payload)
	return "ok"
}
