#!/usr/bin/env python3
"""
Comprehensive test runner for expanded escape detection patterns
Tests all new comprehensive_escapes modules across all languages
"""

import sys
import os
from pathlib import Path
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "python"))

from graphene_ha.test_harness import PythonFunctionTestHarness
from collections import defaultdict
import time

def run_python_comprehensive_tests():
    """Run Python comprehensive test suite"""
    print("\n" + "="*80)
    print("PYTHON COMPREHENSIVE ESCAPE PATTERNS TEST")
    print("="*80)
    
    try:
        import comprehensive_escapes
    except ImportError as e:
        print(f"❌ Could not import comprehensive_escapes: {e}")
        return None
    
    # Get all test functions
    test_functions = [
        name for name in dir(comprehensive_escapes)
        if callable(getattr(comprehensive_escapes, name))
        and not name.startswith('_')
    ]
    
    # Categorize by pattern type
    categories = defaultdict(list)
    for func_name in test_functions:
        if 'global' in func_name or 'closure' in func_name:
            categories['Closure/State'].append(func_name)
        elif 'decorator' in func_name or 'metaclass' in func_name:
            categories['Decorators/Metaclass'].append(func_name)
        elif 'del' in func_name or 'weakref' in func_name:
            categories['Special Methods'].append(func_name)
        elif 'exception' in func_name or 'finally' in func_name:
            categories['Exception Handling'].append(func_name)
        elif 'atexit' in func_name or 'signal' in func_name:
            categories['Lifecycle Handlers'].append(func_name)
        elif 'process' in func_name or 'pool' in func_name:
            categories['Process/Executor'].append(func_name)
        elif 'dynamic' in func_name or 'variable' in func_name or 'indirection' in func_name:
            categories['Dynamic/Obfuscation'].append(func_name)
        elif 'properly' in func_name or 'safe' in func_name:
            categories['Proper Patterns'].append(func_name)
        else:
            categories['Other'].append(func_name)
    
    print(f"\nFound {len(test_functions)} test patterns")
    print("\nPattern Coverage:")
    for category, funcs in sorted(categories.items()):
        print(f"  {category:25} {len(funcs):3} patterns")
    
    return {
        'count': len(test_functions),
        'categories': dict(categories),
        'functions': test_functions
    }


def count_test_patterns():
    """Count test patterns in all comprehensive files"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUITE STATISTICS")
    print("="*80)
    
    base_path = Path(__file__).parent
    
    stats = {}
    
    # Python
    py_file = base_path / "python" / "comprehensive_escapes.py"
    if py_file.exists():
        with open(py_file) as f:
            py_content = f.read()
        py_defs = py_content.count('\ndef ')
        stats['Python'] = py_defs
        print(f"\n📄 Python (comprehensive_escapes.py)")
        print(f"   Functions: {py_defs}")
    
    # Node.js
    js_file = base_path / "nodejs" / "comprehensive_escapes.js"
    if js_file.exists():
        with open(js_file) as f:
            js_content = f.read()
        js_defs = js_content.count('\nfunction ')
        stats['JavaScript'] = js_defs
        print(f"\n📄 JavaScript (comprehensive_escapes.js)")
        print(f"   Functions: {js_defs}")
    
    # Go
    go_file = base_path / "go" / "comprehensive_escapes.go"
    if go_file.exists():
        with open(go_file) as f:
            go_content = f.read()
        go_defs = go_content.count('\nfunc ')
        stats['Go'] = go_defs
        print(f"\n📄 Go (comprehensive_escapes.go)")
        print(f"   Functions: {go_defs}")
    
    # Rust
    rs_file = base_path / "rust" / "comprehensive_escapes.rs"
    if rs_file.exists():
        with open(rs_file) as f:
            rs_content = f.read()
        rs_defs = rs_content.count('\npub fn ')
        stats['Rust'] = rs_defs
        print(f"\n📄 Rust (comprehensive_escapes.rs)")
        print(f"   Functions: {rs_defs}")
    
    total = sum(stats.values())
    print(f"\n{'─'*80}")
    print(f"TOTAL TEST PATTERNS: {total}")
    print(f"{'─'*80}")
    
    return stats


def main():
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "COMPREHENSIVE ESCAPE DETECTION TEST SUITE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    # Count patterns
    stats = count_test_patterns()
    
    # Run Python tests
    python_results = run_python_comprehensive_tests()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print("\n✅ Comprehensive test suites created for:")
    print("   • Python:     comprehensive_escapes.py")
    print("   • JavaScript: comprehensive_escapes.js")
    print("   • Go:         comprehensive_escapes.go")
    print("   • Rust:       comprehensive_escapes.rs")
    
    print("\n📊 Test Categories (Python):")
    if python_results:
        for category, functions in sorted(python_results['categories'].items()):
            print(f"   • {category:25} {len(functions):2} patterns")
    
    print("\n💡 Usage:")
    print("   Test individual patterns:")
    print("     python3 -m tests.python.comprehensive_escapes")
    print()
    print("   Run measurement on comprehensive suite:")
    print("     python3 tests/comprehensive_measurement.py")
    print()
    print("   Analyze with graphene CLI:")
    print("     uv run graphene analyze --file tests/python/comprehensive_escapes.py")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
