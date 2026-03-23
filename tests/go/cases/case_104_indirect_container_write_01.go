package escape_tests

var retainedCase104 = []map[string]string{}

func Case104IndirectContainerWrite01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_01:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase104 = append(retainedCase104, envelope["wrapped"])
	return "ok"
}
