package escape_tests

var retainedCase174 = []map[string]string{}

func Case174IndirectContainerWrite08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "indirect_container_write_08",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "indirect_container_write_08:" + raw,
	}
	envelope := map[string]map[string]string{"wrapped": payload}
	// ESCAPE: indirection writes payload into retained sink.
	retainedCase174 = append(retainedCase174, envelope["wrapped"])
	return "ok"
}
