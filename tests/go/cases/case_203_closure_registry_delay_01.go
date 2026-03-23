package escape_tests

var retainedCase203 = []map[string]string{}

func Case203ClosureRegistryDelay01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_01:" + raw,
	}
	handler := func() string { retainedCase203 = append(retainedCase203, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase203 = append(retainedCase203, map[string]string{"h": payload["task"]})
	return "ok"
}
