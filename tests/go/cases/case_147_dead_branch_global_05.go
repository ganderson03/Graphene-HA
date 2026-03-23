package escape_tests

var retainedCase147 = []map[string]string{}

func Case147DeadBranchGlobal05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_05:" + raw,
	}
	if false {
		retainedCase147 = append(retainedCase147, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
