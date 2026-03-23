package escape_tests

var retainedCase171 = []map[string]string{}

func Case171AliasShadowCache08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_08",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_08:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase171 = append(retainedCase171, alias)
	return "ok"
}
