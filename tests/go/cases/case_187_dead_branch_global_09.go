package escape_tests

var retainedCase187 = []map[string]string{}

func Case187DeadBranchGlobal09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_09",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_09:" + raw,
	}
	if false {
		retainedCase187 = append(retainedCase187, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
