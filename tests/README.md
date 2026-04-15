# Test Programs

This directory contains cross-language escape-analysis case suites used by Graphene HA.

## Suite Layout

- Python: tests/python/cases/
- JavaScript: tests/nodejs/cases/
- Go: tests/go/cases/
- Rust: tests/rust/cases/
- Java: tests/java/src/main/java/com/escape/tests/cases/

Each suite provides labeled functions or methods used for analyzer execution and consistency checks.

## Example Targets

- Python: tests/python/cases/case_001_cache_profile.py:case_001_cache_profile
- JavaScript: tests/nodejs/cases/case_001_cache_profile.js:case001CacheProfile
- Go: tests/go/cases/case_001_cache_profile.go:Case001CacheProfile
- Rust: escape_tests_rust::case_001_cache_profile::case_001_cache_profile
- Java: com.escape.tests.cases.Case001CacheProfile:execute

## Run

```bash
uv run graphene run-all --test-dir tests --generate 10
```

## Case Generation Utilities

```bash
python tests/generate_additional_cases.py
python tests/generate_extreme_cases.py
```
