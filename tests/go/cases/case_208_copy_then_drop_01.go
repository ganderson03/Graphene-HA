package escape_tests

var retainedCase208 = []map[string]string{}

func Case208CopyThenDrop01(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "copy_then_drop_01",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "copy_then_drop_01:" + raw,
	}
	copyObj := map[string]string{}
	for k, v := range payload { copyObj[k] = v }
	_ = copyObj["task"]
	// SAFE: local copy is not retained globally.
	return payload["checksum"]
}
