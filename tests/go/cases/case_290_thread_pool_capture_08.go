package escape_tests

var retainedCase290 = []map[string]string{}

func Case290ThreadPoolCapture08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_08:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase290 = append(retainedCase290, v) }(payload)
	return "ok"
}
