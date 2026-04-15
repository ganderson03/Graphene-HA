#!/usr/bin/env python3
"""Summarize Java static analysis results."""

import re
from pathlib import Path
from collections import defaultdict

# Load all Java static test results
logs_dir = Path('logs/java_static_test/java')
stats = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}

for session_dir in sorted(logs_dir.glob('session_*')):
    readme_file = session_dir / 'README.md'
    if not readme_file.exists():
        continue
    
    # Extract test case name from README
    content = readme_file.read_text()
    if 'Case' not in content:
        continue
    
    # Extract case name from target
    match = re.search(r'Case(\d+[A-Za-z0-9]+)', content)
    if not match:
        continue
    
    case_name = 'Case' + match.group(1)
    
    # Check if it's SAFE by looking for 'SAFE:' in the case code
    case_file = Path('tests/java/src/main/java/com/escape/tests/cases') / (case_name + '.java')
    is_safe = case_file.exists() and 'SAFE:' in case_file.read_text()
    
    # Check if static detected escape (looking for "Total Escapes | 0")
    escapes_detected = 'Total Escapes | 0' not in content and 'Total Escapes' in content
    
    if is_safe and not escapes_detected:
        stats['tn'] += 1
    elif is_safe and escapes_detected:
        stats['fp'] += 1
    elif not is_safe and escapes_detected:
        stats['tp'] += 1
    else:
        stats['fn'] += 1

print('Java Static Analysis Results:')
print(f'  TP: {stats["tp"]}, TN: {stats["tn"]}, FP: {stats["fp"]}, FN: {stats["fn"]}')
print(f'  Total: {sum(stats.values())}')

if sum(stats.values()) > 0:
    acc = (stats['tp'] + stats['tn']) / sum(stats.values())
    prec = stats['tp'] / (stats['tp'] + stats['fp']) if (stats['tp'] + stats['fp']) > 0 else 0.0
    rec = stats['tp'] / (stats['tp'] + stats['fn']) if (stats['tp'] + stats['fn']) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    print(f'  Accuracy: {acc:.1%}, Precision: {prec:.1%}, Recall: {rec:.1%}, F1: {f1:.4f}')
