package escape_tests

var retainedCase131 = []map[string]string{}

func Case131AliasShadowCache04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_04",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_04:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase131 = append(retainedCase131, alias)
	return "ok"
}
