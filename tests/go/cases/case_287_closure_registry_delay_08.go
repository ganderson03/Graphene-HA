package escape_tests

var retainedCase287 = []map[string]string{}

func Case287ClosureRegistryDelay08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_08:" + raw,
	}
	handler := func() string { retainedCase287 = append(retainedCase287, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase287 = append(retainedCase287, map[string]string{"h": payload["task"]})
	return "ok"
}
