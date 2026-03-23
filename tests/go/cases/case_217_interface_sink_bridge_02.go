package escape_tests

var retainedCase217 = []map[string]string{}

type case217Sinker interface{ Put(map[string]string) }
type case217Bridge struct{}

func (case217Bridge) Put(v map[string]string) {
	retainedCase217 = append(retainedCase217, v)
}

func Case217InterfaceSinkBridge02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_02:" + raw,
	}
	var s case217Sinker = case217Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
