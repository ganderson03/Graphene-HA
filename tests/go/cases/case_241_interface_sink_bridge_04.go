package escape_tests

var retainedCase241 = []map[string]string{}

type case241Sinker interface{ Put(map[string]string) }
type case241Bridge struct{}

func (case241Bridge) Put(v map[string]string) {
	retainedCase241 = append(retainedCase241, v)
}

func Case241InterfaceSinkBridge04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_04",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_04:" + raw,
	}
	var s case241Sinker = case241Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
