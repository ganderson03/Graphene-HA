package escape_tests

import "time"

var retainedCase101 = []map[string]string{}

func Case101TransientGoroutineEscape(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}

	payload := map[string]string{
		"task":   "transient_goroutine_escape",
		"entity": "goroutine",
		"stage":  "deferred",
		"input":  raw,
	}

	// ESCAPE: payload escapes via goroutine that outlives caller scope briefly.
	go func() {
		time.Sleep(1 * time.Millisecond)
		retainedCase101 = append(retainedCase101, payload)
	}()

	return "queued"
}
