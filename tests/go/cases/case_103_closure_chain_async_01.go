package escape_tests

var retainedCase103 = []map[string]string{}

func Case103ClosureChainAsync01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_01:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase103 = append(retainedCase103, map[string]string{"h": payload["input"]})
	return "ok"
}
