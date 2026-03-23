package escape_tests

var retainedCase263 = []map[string]string{}

func Case263ClosureRegistryDelay06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_06",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_06:" + raw,
	}
	handler := func() string { retainedCase263 = append(retainedCase263, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase263 = append(retainedCase263, map[string]string{"h": payload["task"]})
	return "ok"
}
