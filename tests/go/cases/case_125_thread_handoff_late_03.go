package escape_tests

var retainedCase125 = []map[string]string{}

func Case125ThreadHandoffLate03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_03:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase125 = append(retainedCase125, p)
	}(payload)
	return "ok"
}
