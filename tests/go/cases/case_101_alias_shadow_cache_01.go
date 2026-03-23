package escape_tests

var retainedCase101 = []map[string]string{}

func Case101AliasShadowCache01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_shadow_cache_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "alias_shadow_cache_01:" + raw,
	}
	alias := payload
	// ESCAPE: alias retained in package-level sink.
	retainedCase101 = append(retainedCase101, alias)
	return "ok"
}
