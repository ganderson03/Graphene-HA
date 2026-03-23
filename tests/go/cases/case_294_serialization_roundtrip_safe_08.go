package escape_tests

var retainedCase294 = []map[string]string{}

func Case294SerializationRoundtripSafe08(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialization_roundtrip_safe_08",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "serialization_roundtrip_safe_08:" + raw,
	}
	flat := payload["task"] + ":" + payload["input"]
	_ = flat
	// SAFE: serialized primitive only.
	return payload["checksum"]
}
