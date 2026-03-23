package escape_tests

var retainedCase191 = []map[string]string{}

func Case191AliasShadowCache10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_10:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase191 = append(retainedCase191, alias)
	return "ok"
}
