package escape_tests

var retainedCase151 = []map[string]string{}

func Case151AliasShadowCache06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_06",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_06:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase151 = append(retainedCase151, alias)
	return "ok"
}
