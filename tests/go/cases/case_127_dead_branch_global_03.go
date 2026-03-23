package escape_tests

var retainedCase127 = []map[string]string{}

func Case127DeadBranchGlobal03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_03:" + raw,
	}
	if false {
		retainedCase127 = append(retainedCase127, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
