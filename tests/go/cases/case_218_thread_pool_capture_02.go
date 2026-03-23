package escape_tests

var retainedCase218 = []map[string]string{}

func Case218ThreadPoolCapture02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "thread_pool_capture_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "thread_pool_capture_02:" + raw,
	}
	// ESCAPE: goroutine captures payload and retains it.
	go func(v map[string]string) { retainedCase218 = append(retainedCase218, v) }(payload)
	return "ok"
}
