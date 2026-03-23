package escape_tests

var retainedCase107 = []map[string]string{}

func Case107DeadBranchGlobal01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "dead_branch_global_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "dead_branch_global_01:" + raw,
	}
	if false {
		retainedCase107 = append(retainedCase107, payload)
	}
	// SAFE: dead branch retention.
	return payload["checksum"]
}
