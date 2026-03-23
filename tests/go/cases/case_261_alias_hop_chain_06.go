package escape_tests

var retainedCase261 = []map[string]string{}

func Case261AliasHopChain06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_hop_chain_06",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "alias_hop_chain_06:" + raw,
	}
	a := payload
	b := a
	c := b
	// ESCAPE: multi-hop alias chain retained globally.
	retainedCase261 = append(retainedCase261, c)
	return "ok"
}
