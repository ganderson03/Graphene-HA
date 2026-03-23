package escape_tests

var retainedCase117 = []map[string]string{}

func Case117DeadBranchGlobal02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_02",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_02:" + raw,
	}
	if false {
		retainedCase117 = append(retainedCase117, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
