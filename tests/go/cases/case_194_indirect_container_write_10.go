package escape_tests

var retainedCase194 = []map[string]string{}

func Case194IndirectContainerWrite10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_10:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase194 = append(retainedCase194, envelope["wrapped"])
	return "ok"
}
