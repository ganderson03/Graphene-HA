package escape_tests

var retainedCase198 = []map[string]string{}

func Case198LocalCacheNamedRetained10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "local_cache_named_retained_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "local_cache_named_retained_10:" + raw,
	}
	retainedLocal := []map[string]string{}
	retainedLocal = append(retainedLocal, payload)
	// SAFE: local slice dies at return.
	return payload["checksum"]
}
