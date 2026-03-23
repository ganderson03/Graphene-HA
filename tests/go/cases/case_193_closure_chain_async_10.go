package escape_tests

var retainedCase193 = []map[string]string{}

func Case193ClosureChainAsync10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_10:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase193 = append(retainedCase193, map[string]string{"h": payload["input"]})
	return "ok"
}
