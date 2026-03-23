package escape_tests

var retainedCase216 = []map[string]string{}

func Case216ContainerHandoffGlobal02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_02:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase216 = append(retainedCase216, box["v"])
	return "ok"
}
