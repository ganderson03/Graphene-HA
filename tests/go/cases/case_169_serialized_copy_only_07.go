package escape_tests

var retainedCase169 = []map[string]string{}

func Case169SerializedCopyOnly07(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialized_copy_only_07",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "serialized_copy_only_07:" + raw,
	}
	serialized := payload["task"] + ":" + payload["input"]
	// SAFE: only primitive string leaves function.
	return serialized
}
