package escape_tests

var retainedCase133 = []map[string]string{}

func Case133ClosureChainAsync04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_04",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_04:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase133 = append(retainedCase133, map[string]string{"h": payload["input"]})
	return "ok"
}
