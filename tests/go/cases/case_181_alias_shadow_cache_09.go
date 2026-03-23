package escape_tests

var retainedCase181 = []map[string]string{}

func Case181AliasShadowCache09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_09",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_09:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase181 = append(retainedCase181, alias)
	return "ok"
}
