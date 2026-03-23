package escape_tests

var retainedCase157 = []map[string]string{}

func Case157DeadBranchGlobal06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_06",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_06:" + raw,
	}
	if false {
		retainedCase157 = append(retainedCase157, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
