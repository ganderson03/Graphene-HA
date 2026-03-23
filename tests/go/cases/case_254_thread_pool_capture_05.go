package escape_tests

var retainedCase254 = []map[string]string{}

func Case254ThreadPoolCapture05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_05:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase254 = append(retainedCase254, v) }(payload)
	return "ok"
}
