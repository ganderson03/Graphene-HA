package escape_tests

var retainedCase239 = []map[string]string{}

func Case239ClosureRegistryDelay04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_04",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_04:" + raw,
	}
	handler := func() string { retainedCase239 = append(retainedCase239, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase239 = append(retainedCase239, map[string]string{"h": payload["task"]})
	return "ok"
}
