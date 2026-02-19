#!/usr/bin/env python3
"""Debug false positives to see what's being detected"""
import sys
sys.path.insert(0, '/home/noelle/Documents/cs/hybrid-escape-leak-analysis/Graphene-HA')

from graphene_ha.test_harness import PythonFunctionTestHarness
from tests.python.no_escape import no_threads, join_thread, join_daemon_thread

# Test no_threads
print("Testing: no_threads")
harness = PythonFunctionTestHarness(no_threads, timeout=5.0, prefer_thread=True)
result = harness.run_test("test")
print(f"  Escape detected: {result.escape_detected}")
print(f"  Escape details: {result.escape_details}")
print()

# Test join_thread  
print("Testing: join_thread")
harness = PythonFunctionTestHarness(join_thread, timeout=5.0, prefer_thread=True)
result = harness.run_test("test")
print(f"  Escape detected: {result.escape_detected}")
print(f"  Escape details: {result.escape_details}")
print()

# Test join_daemon_thread
print("Testing: join_daemon_thread")
harness = PythonFunctionTestHarness(join_daemon_thread, timeout=5.0, prefer_thread=True)
result = harness.run_test("test")
print(f"  Escape detected: {result.escape_detected}")
print(f"  Escape details: {result.escape_details}")
