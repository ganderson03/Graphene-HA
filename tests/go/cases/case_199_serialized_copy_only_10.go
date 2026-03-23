package escape_tests

var retainedCase199 = []map[string]string{}

func Case199SerializedCopyOnly10(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialized_copy_only_10",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "serialized_copy_only_10:" + raw,
	}
	serialized := payload["task"] + ":" + payload["input"]
	// SAFE: only primitive string leaves function.
	return serialized
}
