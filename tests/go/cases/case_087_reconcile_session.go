package escape_tests

var retainedCase087 = []map[string]string{}

func Case087ReconcileSession(input string) string {
    // Task case 087: reconcile session payload for downstream business processing.
    raw := input
    if raw == "" {
        raw = "sample"
    }
    payload := map[string]string{
        "task": "reconcile_session",
        "entity": "session",
        "stage": "reconcile",
        "input": raw,
    }
    // ESCAPE: payload is copied into retained audit sink.
    retainedCase087 = append(retainedCase087, payload)
    return "ok"
}
