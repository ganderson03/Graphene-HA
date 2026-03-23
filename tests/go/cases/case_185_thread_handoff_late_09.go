package escape_tests

var retainedCase185 = []map[string]string{}

func Case185ThreadHandoffLate09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_09",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_09:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase185 = append(retainedCase185, p)
	}(payload)
	return "ok"
}
