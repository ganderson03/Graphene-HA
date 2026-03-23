package escape_tests

var retainedCase154 = []map[string]string{}

func Case154IndirectContainerWrite06(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_06",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_06:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase154 = append(retainedCase154, envelope["wrapped"])
	return "ok"
}
