"""
Paper-inspired case 101: interprocedural precision challenge.
Inspired by Choi et al. (connection graphs/interprocedural summaries)
and Weingarten et al. (context-sensitive partial escape analysis).
"""


def _consume_locally(payload):
    # This helper only reads payload and returns a primitive.
    return payload.get("task", "") + ":" + payload.get("input", "")


def case_101_interprocedural_precision(input_data):
    raw = input_data or "sample"
    payload = {
        "task": "interprocedural_precision",
        "entity": "precision",
        "stage": "local_read",
        "input": raw,
    }
    _ = _consume_locally(payload)
    # SAFE: payload is not stored globally, returned, or captured asynchronously.
    return payload["task"] + ":" + payload["input"]
