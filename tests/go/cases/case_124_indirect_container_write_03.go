package escape_tests

var retainedCase124 = []map[string]string{}

func Case124IndirectContainerWrite03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_03:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase124 = append(retainedCase124, envelope["wrapped"])
	return "ok"
}
