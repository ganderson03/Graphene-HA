package escape_tests

var retainedCase276 = []map[string]string{}

func Case276ContainerHandoffGlobal07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_07:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase276 = append(retainedCase276, box["v"])
	return "ok"
}
