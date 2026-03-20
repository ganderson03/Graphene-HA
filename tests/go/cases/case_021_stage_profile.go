package escape_tests

var retainedCase021 = []map[string]string{}

func Case021StageProfile(input string) string {
    // Task case 021: stage profile payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "stage_profile",
        "entity": "profile",
        "stage": "stage",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase021 = append(retainedCase021, payload)
    return "ok"
}
