package escape_tests

var retainedCase163 = []map[string]string{}

func Case163ClosureChainAsync07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_07",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_07:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase163 = append(retainedCase163, map[string]string{"h": payload["input"]})
	return "ok"
}
