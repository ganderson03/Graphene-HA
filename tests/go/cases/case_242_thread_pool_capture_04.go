package escape_tests

var retainedCase242 = []map[string]string{}

func Case242ThreadPoolCapture04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_04",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_04:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase242 = append(retainedCase242, v) }(payload)
	return "ok"
}
