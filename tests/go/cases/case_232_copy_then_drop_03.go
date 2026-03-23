package escape_tests

var retainedCase232 = []map[string]string{}

func Case232CopyThenDrop03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "copy_then_drop_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "copy_then_drop_03:" + raw,
	}
	copyObj := map[string]string{}
	for k, v := range payload { copyObj[k] = v }
	_ = copyObj["task"]
	// SAFE: local copy is not retained globally.
	return payload["checksum"]
}
