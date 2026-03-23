package escape_tests

var retainedCase114 = []map[string]string{}

func Case114IndirectContainerWrite02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_02",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_02:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase114 = append(retainedCase114, envelope["wrapped"])
	return "ok"
}
