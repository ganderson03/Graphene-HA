package escape_tests

var retainedCase113 = []map[string]string{}

func Case113ClosureChainAsync02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_02",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_02:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase113 = append(retainedCase113, map[string]string{"h": payload["input"]})
	return "ok"
}
