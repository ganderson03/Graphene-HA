package escape_tests

var retainedCase274 = []map[string]string{}

func Case274HelperSinkDispatch07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_07:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase274 = append(retainedCase274, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
