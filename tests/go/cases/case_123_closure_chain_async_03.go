package escape_tests

var retainedCase123 = []map[string]string{}

func Case123ClosureChainAsync03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "closure_chain_async_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "closure_chain_async_03:" + raw,
	}
	handler := func() string { return payload["input"] }
	_ = handler
	// ESCAPE: closure payload persisted indirectly via retained metadata map.
	retainedCase123 = append(retainedCase123, map[string]string{"h": payload["input"]})
	return "ok"
}
