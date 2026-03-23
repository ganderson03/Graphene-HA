package escape_tests

var retainedCase183 = []map[string]string{}

func Case183ClosureChainAsync09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_09",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_09:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase183 = append(retainedCase183, map[string]string{"h": payload["input"]})
	return "ok"
}
