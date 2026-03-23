package escape_tests

var retainedCase240 = []map[string]string{}

func Case240ContainerHandoffGlobal04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_04",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_04:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase240 = append(retainedCase240, box["v"])
	return "ok"
}
