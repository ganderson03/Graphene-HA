package escape_tests

var retainedCase285 = []map[string]string{}

func Case285AliasHopChain08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_hop_chain_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "alias_hop_chain_08:" + raw,
	}
	a := payload
	b := a
	c := b
	// ESCAPE: multi-hop alias chain retained globally.
	retainedCase285 = append(retainedCase285, c)
	return "ok"
}
