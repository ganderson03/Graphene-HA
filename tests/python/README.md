# Python Data Escape Tests

## Primary suite

- cases/

This directory contains 100 annotated modules (`case_001_cache_profile.py` ... `case_100__ledger.py`).
Each module exports one function named after the file, for example `case_001_cache_profile`.

Annotations used inside each case:
- ESCAPE: object leaves local scope
- SAFE: object remains local and only primitive output leaves

## Examples

```bash
uv run graphene analyze tests/python/cases/case_001_cache_profile.py:case_001_cache_profile --input "sample"
uv run graphene analyze tests/python/cases/case_005_cache_ticket.py:case_005_cache_ticket --input "sample"
```
