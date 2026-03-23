package escape_tests

var retainedCase234 = []map[string]string{}

func Case234SerializationRoundtripSafe03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "serialization_roundtrip_safe_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "serialization_roundtrip_safe_03:" + raw,
	}
	flat := payload["task"] + ":" + payload["input"]
	_ = flat
	// SAFE: serialized primitive only.
	return payload["checksum"]
}
