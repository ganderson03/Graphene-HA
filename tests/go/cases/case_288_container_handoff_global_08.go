package escape_tests

var retainedCase288 = []map[string]string{}

func Case288ContainerHandoffGlobal08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_08:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase288 = append(retainedCase288, box["v"])
	return "ok"
}
