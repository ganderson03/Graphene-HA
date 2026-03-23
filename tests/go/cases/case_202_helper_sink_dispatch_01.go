package escape_tests

var retainedCase202 = []map[string]string{}

func Case202HelperSinkDispatch01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_01:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase202 = append(retainedCase202, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
