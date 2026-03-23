package escape_tests

var retainedCase286 = []map[string]string{}

func Case286HelperSinkDispatch08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_08:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase286 = append(retainedCase286, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
