package escape_tests

var retainedCase184 = []map[string]string{}

func Case184IndirectContainerWrite09(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_09",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_09:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase184 = append(retainedCase184, envelope["wrapped"])
	return "ok"
}
