package escape_tests

var retainedCase145 = []map[string]string{}

func Case145ThreadHandoffLate05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_05:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase145 = append(retainedCase145, p)
	}(payload)
	return "ok"
}
