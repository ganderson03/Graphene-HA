package escape_tests

var retainedCase091 = []map[string]string{}

func Case091ReconcileProfile(input string) string {
    // Task case 091: reconcile profile payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "reconcile_profile",
        "entity": "profile",
        "stage": "reconcile",
        "input": raw,
    }
    // ESCAPE: payload is promoted to package-level retained cache.
    retainedCase091 = append(retainedCase091, payload)
    return "ok"
}
