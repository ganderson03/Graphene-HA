package escape_tests

var retainedCase266 = []map[string]string{}

func Case266ThreadPoolCapture06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_06",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_06:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase266 = append(retainedCase266, v) }(payload)
	return "ok"
}
