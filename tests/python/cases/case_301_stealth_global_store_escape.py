"""Adversarial spoiler case 301: stealth global store escape."""

GLOBAL_STORE = {}


def case_301_stealth_global_store_escape(input_data):
    raw = input_data or "sample"
    payload = {
        "task": "stealth_global_store_escape",
        "entity": "spoiler",
        "stage": "adversarial",
        "input": raw,
        "checksum": f"stealth:{len(raw)}",
    }

    carrier = {"value": payload}
    # ESCAPE: indirect global write via globals() map and alias carrier.
    globals()["GLOBAL_STORE"]["k301"] = carrier["value"]
    return "ok"
