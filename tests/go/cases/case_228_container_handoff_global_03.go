package escape_tests

var retainedCase228 = []map[string]string{}

func Case228ContainerHandoffGlobal03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_03:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase228 = append(retainedCase228, box["v"])
	return "ok"
}
