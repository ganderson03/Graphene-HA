package escape_tests

var retainedCase277 = []map[string]string{}

type case277Sinker interface{ Put(map[string]string) }
type case277Bridge struct{}

func (case277Bridge) Put(v map[string]string) {
	retainedCase277 = append(retainedCase277, v)
}

func Case277InterfaceSinkBridge07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_07",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_07:" + raw,
	}
	var s case277Sinker = case277Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
