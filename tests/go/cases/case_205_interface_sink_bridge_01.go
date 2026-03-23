package escape_tests

var retainedCase205 = []map[string]string{}

type case205Sinker interface{ Put(map[string]string) }
type case205Bridge struct{}

func (case205Bridge) Put(v map[string]string) {
	retainedCase205 = append(retainedCase205, v)
}

func Case205InterfaceSinkBridge01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_01:" + raw,
	}
	var s case205Sinker = case205Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
