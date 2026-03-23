package escape_tests

var retainedCase165 = []map[string]string{}

func Case165ThreadHandoffLate07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_07",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_07:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase165 = append(retainedCase165, p)
	}(payload)
	return "ok"
}
