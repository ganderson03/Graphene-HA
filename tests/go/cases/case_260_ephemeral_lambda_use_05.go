package escape_tests

var retainedCase260 = []map[string]string{}

func Case260EphemeralLambdaUse05(input string) string {
	raw := input
	if raw == "" {
		raw = "sample"
	}
	payload := map[string]string{
		"task": "ephemeral_lambda_use_05",
		"entity": "extreme",
		"stage": "stress",
		"input": raw,
		"checksum": "ephemeral_lambda_use_05:" + raw,
	}
	f := func() string { return payload["task"] }
	_ = f()
	// SAFE: immediate lambda usage only.
	return payload["checksum"]
}
