package escape_tests

var retainedCase233 = []map[string]string{}

func Case233LocalCloneNamedRetained03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "local_clone_named_retained_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "local_clone_named_retained_03:" + raw,
	}
	retainedLocal := []map[string]string{payload}
	_ = retainedLocal
	// SAFE: misleading local name only.
	return payload["checksum"]
}
