package escape_tests

var retainedCase141 = []map[string]string{}

func Case141AliasShadowCache05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_05:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase141 = append(retainedCase141, alias)
	return "ok"
}
