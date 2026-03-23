package escape_tests

var retainedCase144 = []map[string]string{}

func Case144IndirectContainerWrite05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_05:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase144 = append(retainedCase144, envelope["wrapped"])
	return "ok"
}
