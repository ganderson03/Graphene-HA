package escape_tests

var retainedCase275 = []map[string]string{}

func Case275ClosureRegistryDelay07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_07:" + raw,
	}
	handler := func() string { retainedCase275 = append(retainedCase275, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase275 = append(retainedCase275, map[string]string{"h": payload["task"]})
	return "ok"
}
