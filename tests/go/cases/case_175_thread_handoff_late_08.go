package escape_tests

var retainedCase175 = []map[string]string{}

func Case175ThreadHandoffLate08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_08",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_08:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase175 = append(retainedCase175, p)
	}(payload)
	return "ok"
}
