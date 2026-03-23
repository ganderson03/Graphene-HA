package escape_tests

var retainedCase143 = []map[string]string{}

func Case143ClosureChainAsync05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_05:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase143 = append(retainedCase143, map[string]string{"h": payload["input"]})
	return "ok"
}
