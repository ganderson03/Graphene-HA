"""Adversarial spoiler case 302: setattr indirection escape."""

import builtins


def case_302_indirect_setattr_escape(input_data):
    raw = input_data or "sample"
    payload = {
        "task": "indirect_setattr_escape",
        "entity": "spoiler",
        "stage": "adversarial",
        "input": raw,
        "checksum": f"setattr:{len(raw)}",
    }

    # ESCAPE: payload escapes through dynamic attribute assignment on module object.
    setattr(builtins, "_graphene_spoiler_302", payload)
    return "ok"
