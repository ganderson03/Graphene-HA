package escape_tests

var retainedCase225 = []map[string]string{}

func Case225AliasHopChain03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "alias_hop_chain_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "alias_hop_chain_03:" + raw,
	}
	a := payload
	b := a
	c := b
	// ESCAPE: multi-hop alias chain retained globally.
	retainedCase225 = append(retainedCase225, c)
	return "ok"
}
