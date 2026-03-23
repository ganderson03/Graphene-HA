package escape_tests

var retainedCase236 = []map[string]string{}

func Case236EphemeralLambdaUse03(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "ephemeral_lambda_use_03",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "ephemeral_lambda_use_03:" + raw,
	}
	f := func() string { return payload["task"] }
	_ = f()
	// SAFE: immediate lambda usage only.
	return payload["checksum"]
}
