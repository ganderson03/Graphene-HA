package escape_tests

var retainedCase153 = []map[string]string{}

func Case153ClosureChainAsync06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_06",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_06:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase153 = append(retainedCase153, map[string]string{"h": payload["input"]})
	return "ok"
}
