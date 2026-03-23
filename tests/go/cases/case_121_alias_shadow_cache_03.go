package escape_tests

var retainedCase121 = []map[string]string{}

func Case121AliasShadowCache03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_03:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase121 = append(retainedCase121, alias)
	return "ok"
}
