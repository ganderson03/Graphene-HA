package escape_tests

var retainedCase214 = []map[string]string{}

func Case214HelperSinkDispatch02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "helper_sink_dispatch_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "helper_sink_dispatch_02:" + raw,
	}
	sink := func(obj map[string]string) { retainedCase214 = append(retainedCase214, obj) }
	// ESCAPE: helper sink function hides retention edge.
	sink(payload)
	return "ok"
}
