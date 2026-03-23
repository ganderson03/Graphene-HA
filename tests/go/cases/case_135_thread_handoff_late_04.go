package escape_tests

var retainedCase135 = []map[string]string{}

func Case135ThreadHandoffLate04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_04",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_04:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase135 = append(retainedCase135, p)
	}(payload)
	return "ok"
}
