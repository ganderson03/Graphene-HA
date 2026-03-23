package escape_tests

var retainedCase299 = []map[string]string{}

func Case299ClosureRegistryDelay09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_09",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_09:" + raw,
	}
	handler := func() string { retainedCase299 = append(retainedCase299, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase299 = append(retainedCase299, map[string]string{"h": payload["task"]})
	return "ok"
}
