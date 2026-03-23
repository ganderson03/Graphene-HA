"""Adversarial spoiler case 303: module proxy escape."""

import sys


def case_303_module_proxy_escape(input_data):
    raw = input_data or "sample"
    payload = {
        "task": "module_proxy_escape",
        "entity": "spoiler",
        "stage": "adversarial",
        "input": raw,
        "checksum": f"module:{len(raw)}",
    }

    module_obj = sys.modules[__name__]
    # ESCAPE: dynamic module-level sink with non-retained naming.
    setattr(module_obj, "sink_303", payload)
    return "ok"
