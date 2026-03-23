package escape_tests

var retainedCase278 = []map[string]string{}

func Case278ThreadPoolCapture07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_07:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase278 = append(retainedCase278, v) }(payload)
	return "ok"
}
