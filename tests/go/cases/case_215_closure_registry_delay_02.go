package escape_tests

var retainedCase215 = []map[string]string{}

func Case215ClosureRegistryDelay02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_registry_delay_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "closure_registry_delay_02:" + raw,
	}
	handler := func() string { retainedCase215 = append(retainedCase215, payload); return payload["input"] }
	_ = handler
	// ESCAPE: retained closure-like dispatch.
	retainedCase215 = append(retainedCase215, map[string]string{"h": payload["task"]})
	return "ok"
}
