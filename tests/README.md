# Test Programs

Language test programs for object/data escape analysis.

## Language Reference

### 300+ Case Suites

- **Python**: tests/python/cases/case_001_cache_profile.py ... case_300_ephemeral_lambda_use_09.py
- **JavaScript**: tests/nodejs/cases/case_001_cache_profile.js ... case_300_ephemeral_lambda_use_09.js
- **Go**: tests/go/cases/case_001_cache_profile.go ... case_300_ephemeral_lambda_use_09.go
- **Rust**: tests/rust/cases/case_001_cache_profile.rs ... case_300_ephemeral_lambda_use_09.rs
- **Java**: tests/java/src/main/java/com/escape/tests/cases/Case001CacheProfile.java ... Case300EphemeralLambdaUse09.java

Each suite provides:
- 300+ realistic and adversarial functions/methods
- inline ESCAPE or SAFE comments
- mixed patterns (global retention, retained sink calls, closure capture, local-safe behavior)
- stress variants designed to provoke false positives/false negatives

### Case Generation Helpers

Regenerate expanded suites with:

```bash
python tests/generate_additional_cases.py
python tests/generate_extreme_cases.py
```

### Example Targets by Language

- **Python**: tests/python/cases/case_001_cache_profile.py:case_001_cache_profile
- **JavaScript**: tests/nodejs/cases/case_001_cache_profile.js:case001CacheProfile
- **Go**: tests/go/cases/case_001_cache_profile.go:Case001CacheProfile
- **Rust**: escape_tests_rust::case_001_cache_profile::case_001_cache_profile
- **Java**: com.escape.tests.cases.Case001CacheProfile:execute

## Run

```bash
uv run graphene run-all --test-dir tests --generate 10
```

For language-specific target naming conventions, see the README file in each language folder.
