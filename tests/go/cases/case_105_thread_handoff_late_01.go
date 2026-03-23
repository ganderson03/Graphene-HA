package escape_tests

var retainedCase105 = []map[string]string{}

func Case105ThreadHandoffLate01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_01:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase105 = append(retainedCase105, p)
	}(payload)
	return "ok"
}
