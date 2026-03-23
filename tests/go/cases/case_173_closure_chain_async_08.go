package escape_tests

var retainedCase173 = []map[string]string{}

func Case173ClosureChainAsync08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_08",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_08:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase173 = append(retainedCase173, map[string]string{"h": payload["input"]})
	return "ok"
}
