package escape_tests

var retainedCase273 = []map[string]string{}

func Case273AliasHopChain07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_hop_chain_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "alias_hop_chain_07:" + raw,
	}
	a := payload
	b := a
	c := b
	// ESCAPE: multi-hop alias chain retained globally.
	retainedCase273 = append(retainedCase273, c)
	return "ok"
}
