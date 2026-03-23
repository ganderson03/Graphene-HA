package escape_tests

var retainedCase204 = []map[string]string{}

func Case204ContainerHandoffGlobal01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "container_handoff_global_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "container_handoff_global_01:" + raw,
	}
	box := map[string]map[string]string{"v": payload}
	// ESCAPE: nested container handoff retained globally.
	retainedCase204 = append(retainedCase204, box["v"])
	return "ok"
}
