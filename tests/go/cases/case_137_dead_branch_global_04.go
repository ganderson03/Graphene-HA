package escape_tests

var retainedCase137 = []map[string]string{}

func Case137DeadBranchGlobal04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_04",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_04:" + raw,
	}
	if false {
		retainedCase137 = append(retainedCase137, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
