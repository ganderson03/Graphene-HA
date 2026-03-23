package escape_tests

var retainedCase109 = []map[string]string{}

func Case109SerializedCopyOnly01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialized_copy_only_01",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "serialized_copy_only_01:" + raw,
	}
	serialized := payload["task"] + ":" + payload["input"]
	// SAFE: only primitive string leaves function.
	return serialized
}
