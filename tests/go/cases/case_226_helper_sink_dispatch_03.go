package escape_tests

var retainedCase226 = []map[string]string{}

func Case226HelperSinkDispatch03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_03:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase226 = append(retainedCase226, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
