package escape_tests

var retainedCase164 = []map[string]string{}

func Case164IndirectContainerWrite07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_07",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_07:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase164 = append(retainedCase164, envelope["wrapped"])
	return "ok"
}
