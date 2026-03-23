package escape_tests

var retainedCase249 = []map[string]string{}

func Case249AliasHopChain05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_hop_chain_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "alias_hop_chain_05:" + raw,
	}
	a := payload
	b := a
	c := b
	// ESCAPE: multi-hop alias chain retained globally.
	retainedCase249 = append(retainedCase249, c)
	return "ok"
}
