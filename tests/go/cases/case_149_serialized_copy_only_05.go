package escape_tests

var retainedCase149 = []map[string]string{}

func Case149SerializedCopyOnly05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialized_copy_only_05",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "serialized_copy_only_05:" + raw,
	}
	serialized := payload["task"] + ":" + payload["input"]
	// SAFE: only primitive string leaves function.
	return serialized
}
