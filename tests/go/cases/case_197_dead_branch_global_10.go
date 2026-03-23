package escape_tests

var retainedCase197 = []map[string]string{}

func Case197DeadBranchGlobal10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_10:" + raw,
	}
	if false {
		retainedCase197 = append(retainedCase197, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
