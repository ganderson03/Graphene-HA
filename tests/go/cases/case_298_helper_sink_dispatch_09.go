package escape_tests

var retainedCase298 = []map[string]string{}

func Case298HelperSinkDispatch09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_09",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_09:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase298 = append(retainedCase298, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
