package escape_tests

var retainedCase238 = []map[string]string{}

func Case238HelperSinkDispatch04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_04",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_04:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase238 = append(retainedCase238, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
