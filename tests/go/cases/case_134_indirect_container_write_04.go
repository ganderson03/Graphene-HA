package escape_tests

var retainedCase134 = []map[string]string{}

func Case134IndirectContainerWrite04(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_04",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_04:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase134 = append(retainedCase134, envelope["wrapped"])
	return "ok"
}
