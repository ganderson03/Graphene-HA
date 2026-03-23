package escape_tests

var retainedCase265 = []map[string]string{}

type case265Sinker interface{ Put(map[string]string) }
type case265Bridge struct{}

func (case265Bridge) Put(v map[string]string) {
	retainedCase265 = append(retainedCase265, v)
}

func Case265InterfaceSinkBridge06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_06",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_06:" + raw,
	}
	var s case265Sinker = case265Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
