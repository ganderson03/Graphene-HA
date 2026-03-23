package escape_tests

var retainedCase111 = []map[string]string{}

func Case111AliasShadowCache02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_02",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_02:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase111 = append(retainedCase111, alias)
	return "ok"
}
