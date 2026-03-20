# Test Programs

Language test programs for object/data escape analysis.

## Language Reference

### 100-Case Suites

- **Python**: tests/python/cases/case_001_cache_profile.py ... case_100__ledger.py
- **JavaScript**: tests/nodejs/cases/case_001_cache_profile.js ... case_100__ledger.js
- **Go**: tests/go/cases/case_001_cache_profile.go ... case_100__ledger.go
- **Rust**: tests/rust/cases/case_001_cache_profile.rs ... case_100__ledger.rs
- **Java**: tests/java/src/main/java/com/escape/tests/cases/Case001CacheProfile.java ... Case100Ledger.java

Each suite provides:
- 100 realistic functions/methods
- inline ESCAPE or SAFE comments
- mixed patterns (global retention, retained sink calls, closure capture, local-safe behavior)

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
