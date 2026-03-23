package escape_tests

var retainedCase115 = []map[string]string{}

func Case115ThreadHandoffLate02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_02",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_02:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase115 = append(retainedCase115, p)
	}(payload)
	return "ok"
}
