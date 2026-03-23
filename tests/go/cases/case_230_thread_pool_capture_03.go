package escape_tests

var retainedCase230 = []map[string]string{}

func Case230ThreadPoolCapture03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_03:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase230 = append(retainedCase230, v) }(payload)
	return "ok"
}
