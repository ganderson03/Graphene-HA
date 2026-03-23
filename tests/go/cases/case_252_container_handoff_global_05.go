package escape_tests

var retainedCase252 = []map[string]string{}

func Case252ContainerHandoffGlobal05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_05:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase252 = append(retainedCase252, box["v"])
	return "ok"
}
