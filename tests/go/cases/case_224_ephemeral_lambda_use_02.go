package escape_tests

var retainedCase224 = []map[string]string{}

func Case224EphemeralLambdaUse02(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "ephemeral_lambda_use_02",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "ephemeral_lambda_use_02:" + raw,
	}
	f := func() string { return payload["task"] }
	_ = f()
	// SAFE: immediate lambda usage only.
	return payload["checksum"]
}
