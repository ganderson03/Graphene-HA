package escape_tests

var retainedCase289 = []map[string]string{}

type case289Sinker interface{ Put(map[string]string) }
type case289Bridge struct{}

func (case289Bridge) Put(v map[string]string) {
	retainedCase289 = append(retainedCase289, v)
}

func Case289InterfaceSinkBridge08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_08:" + raw,
	}
	var s case289Sinker = case289Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
