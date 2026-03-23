package escape_tests

var retainedCase227 = []map[string]string{}

func Case227ClosureRegistryDelay03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_03:" + raw,
	}
	handler := func() string { retainedCase227 = append(retainedCase227, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase227 = append(retainedCase227, map[string]string{"h": payload["task"]})
	return "ok"
}
