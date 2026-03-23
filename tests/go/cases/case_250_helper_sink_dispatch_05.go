package escape_tests

var retainedCase250 = []map[string]string{}

func Case250HelperSinkDispatch05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_05:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase250 = append(retainedCase250, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
