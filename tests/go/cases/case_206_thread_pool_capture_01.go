package escape_tests

var retainedCase206 = []map[string]string{}

func Case206ThreadPoolCapture01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_01:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase206 = append(retainedCase206, v) }(payload)
	return "ok"
}
