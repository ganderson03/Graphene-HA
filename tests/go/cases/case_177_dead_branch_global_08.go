package escape_tests

var retainedCase177 = []map[string]string{}

func Case177DeadBranchGlobal08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_08",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_08:" + raw,
	}
	if false {
		retainedCase177 = append(retainedCase177, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
