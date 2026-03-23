package escape_tests

var retainedCase229 = []map[string]string{}

type case229Sinker interface{ Put(map[string]string) }
type case229Bridge struct{}

func (case229Bridge) Put(v map[string]string) {
	retainedCase229 = append(retainedCase229, v)
}

func Case229InterfaceSinkBridge03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "interface_sink_bridge_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "interface_sink_bridge_03:" + raw,
	}
	var s case229Sinker = case229Bridge{}
	// ESCAPE: interface bridge dispatch to sink.
	s.Put(payload)
	return "ok"
}
