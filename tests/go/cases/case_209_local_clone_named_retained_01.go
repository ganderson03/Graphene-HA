package escape_tests

var retainedCase209 = []map[string]string{}

func Case209LocalCloneNamedRetained01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "local_clone_named_retained_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "local_clone_named_retained_01:" + raw,
	}
	retainedLocal := []map[string]string{payload}
	_ = retainedLocal
	// SAFE: misleading local name only.
	return payload["checksum"]
}
