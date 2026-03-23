package escape_tests

var retainedCase262 = []map[string]string{}

func Case262HelperSinkDispatch06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_06",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_06:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase262 = append(retainedCase262, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
