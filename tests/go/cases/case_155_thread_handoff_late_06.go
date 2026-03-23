package escape_tests

var retainedCase155 = []map[string]string{}

func Case155ThreadHandoffLate06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_handoff_late_06",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "thread_handoff_late_06:" + raw,
	}
	// ESCAPE: goroutine captures payload and appends to retained sink.
	go func(p map[string]string) {
		retainedCase155 = append(retainedCase155, p)
	}(payload)
	return "ok"
}
