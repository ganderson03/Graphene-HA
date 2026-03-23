package escape_tests

var retainedCase129 = []map[string]string{}

func Case129SerializedCopyOnly03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialized_copy_only_03",
		"entity": "stress",
		"stage": "evaluation",
		"input": raw,
		"checksum": "serialized_copy_only_03:" + raw,
	}
	serialized := payload["task"] + ":" + payload["input"]
	// SAFE: only primitive string leaves function.
	return serialized
}
