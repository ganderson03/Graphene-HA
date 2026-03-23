package escape_tests

var retainedCase281 = []map[string]string{}

func Case281LocalCloneNamedRetained07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "local_clone_named_retained_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "local_clone_named_retained_07:" + raw,
	}
	retainedLocal := []map[string]string{payload}
	_ = retainedLocal
	// SAFE: misleading local name only.
	return payload["checksum"]
}
