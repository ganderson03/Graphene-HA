package escape_tests

var retainedCase251 = []map[string]string{}

func Case251ClosureRegistryDelay05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_05:" + raw,
	}
	handler := func() string { retainedCase251 = append(retainedCase251, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase251 = append(retainedCase251, map[string]string{"h": payload["task"]})
	return "ok"
}
