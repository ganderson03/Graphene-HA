package escape_tests

var retainedCase253 = []map[string]string{}

type case253Sinker interface{ Put(map[string]string) }
type case253Bridge struct{}

func (case253Bridge) Put(v map[string]string) {
	retainedCase253 = append(retainedCase253, v)
}

func Case253InterfaceSinkBridge05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_05:" + raw,
	}
	var s case253Sinker = case253Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
