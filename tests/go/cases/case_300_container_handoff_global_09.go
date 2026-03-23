package escape_tests

var retainedCase300 = []map[string]string{}

func Case300ContainerHandoffGlobal09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_09",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_09:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase300 = append(retainedCase300, box["v"])
	return "ok"
}
