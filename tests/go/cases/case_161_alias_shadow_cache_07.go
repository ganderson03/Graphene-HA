package escape_tests

var retainedCase161 = []map[string]string{}

func Case161AliasShadowCache07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_07",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_07:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase161 = append(retainedCase161, alias)
	return "ok"
}
