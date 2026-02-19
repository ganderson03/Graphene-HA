#!/usr/bin/env python3
import argparse
import importlib
import importlib.util
import inspect
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .test_harness import PythonFunctionTestHarness
from .vulnerability_detector import VulnerabilityDetector
from .help import show_help
from .logging_util import TestingLogger
from .constants import (
    INPUT_PATTERNS,
    DEFAULT_REPEAT_COUNT,
    DEFAULT_GENERATE_COUNT,
    DEFAULT_TIMEOUT,
    DEFAULT_LOG_DIR,
    DEFAULT_TEST_DIR,
    PYTHON_TEST_DIR,
)

ROOT_DIR = Path(__file__).resolve().parent.parent


def _validate_positive_float(value):
    val = float(value)
    if val <= 0:
        raise argparse.ArgumentTypeError(f"timeout must be positive (got {val})")
    return val


def _validate_positive_int(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError(f"repeat must be positive (got {val})")
    return val


@dataclass
class EscapeReport:
    total_tests:int
    crashes:int
    successes:int
    timeouts:int
    escapes:int
    genuine_escapes:int
    crash_rate:float
    vulnerabilities:list


def _load_function(target):
    if ":" not in target:
        raise ValueError("Target must be in module:function or path.py:function form")
    module_spec, func_name = target.split(":",1)
    if module_spec.endswith(".py"):
        module_path=Path(module_spec)
        if not module_path.exists():
            raise FileNotFoundError(f"File not found: {module_path}")
        module_name=module_path.stem
        spec=importlib.util.spec_from_file_location(module_name,str(module_path))
        module=importlib.util.module_from_spec(spec)
        sys.modules[module_name]=module
        spec.loader.exec_module(module)
    else:
        module=importlib.import_module(module_spec)
    func=getattr(module,func_name,None)
    if not callable(func):
        raise ValueError(f"Function not found or not callable: {module_spec}:{func_name}")
    return func


def _discover_tests(root_dir):
    test_dir=Path(root_dir)/"tests"/"python"
    if not test_dir.exists():
        raise FileNotFoundError(f"Missing tests/python folder: {test_dir}")
    tests=[]
    for path in sorted(test_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name=f"tests.python.{path.stem}"
        spec=importlib.util.spec_from_file_location(module_name,str(path))
        module=importlib.util.module_from_spec(spec)
        sys.modules[module_name]=module
        spec.loader.exec_module(module)
        requires_thread=bool(getattr(module,"REQUIRES_THREAD_MODE",False))
        requires_main=bool(getattr(module,"REQUIRES_MAIN_THREAD",False))
        for name,func in inspect.getmembers(module,inspect.isfunction):
            if func.__module__!=module.__name__:
                continue
            if name.startswith("_"):
                continue
            tests.append((f"{path}:{name}",func,requires_thread,requires_main))
    return tests


def _generate_inputs(count,seed=None):
    rng=random.Random(seed)
    return [rng.choice(INPUT_PATTERNS) for _ in range(count)]


def _run_tests(func,inputs,repeat,timeout,logger,prefer_thread=False,prefer_main_thread=False):
    harness=PythonFunctionTestHarness(func,timeout=timeout,prefer_thread=prefer_thread,prefer_main_thread=prefer_main_thread)
    detector=VulnerabilityDetector()
    results=[]
    total_runs=len(inputs)*repeat
    logger.log_session_start(f"{func.__module__}:{func.__name__}",inputs,total_runs,timeout)
    attempt=0
    for _ in range(repeat):
        for input_data in inputs:
            attempt+=1
            start=time.time()
            result=harness.run_test(input_data)
            exec_time=(time.time()-start)*1000
            vuln=detector.analyze_result(result)
            vulnerabilities=[vuln] if vuln else []
            logger.log_attempt(attempt,input_data,result,vulnerabilities,exec_time)
            results.append(result)
    cat=detector.categorize_results(results)
    report=EscapeReport(total_tests=cat["total_tests"],crashes=cat["crashes"],successes=cat["successes"],timeouts=cat["timeouts"],escapes=cat.get("escapes",0),genuine_escapes=cat.get("genuine_escapes",0),crash_rate=cat["crash_rate"],vulnerabilities=cat["vulnerabilities"])
    logger.log_session_end(report)
    return report


def _configure_logger(logger,verbose):
    if not verbose:
        return
    logger.logger.setLevel(logging.DEBUG)
    for handler in logger.logger.handlers:
        if isinstance(handler,logging.StreamHandler):
            handler.setLevel(logging.DEBUG)


def _ensure_rust_binary():
    """Build Rust binary if it doesn't exist."""
    root_dir=Path(__file__).resolve().parent.parent
    binary_name="graphene-ha.exe" if os.name=="nt" else "graphene-ha"
    binary_path=root_dir/"target"/"release"/binary_name
    
    if not binary_path.exists():
        print(f"Building Rust binary (first time only)...",file=sys.stderr)
        result=subprocess.run(
            ["cargo","build","--release"],
            cwd=root_dir,
            check=False
        )
        if result.returncode!=0:
            raise RuntimeError("Failed to build Rust binary. Run 'cargo build --release' manually.")
        if not binary_path.exists():
            raise FileNotFoundError(f"Build succeeded but binary not found: {binary_path}")
    
    return binary_path


def _should_use_rust_binary(args,command):
    """Determine if we should delegate to Rust binary."""
    # Always use Rust for list command
    if command=="list":
        return True
    
    # Use Rust for static analysis
    if hasattr(args,"analysis_mode") and args.analysis_mode in ("static","both"):
        return True
    
    # Use Rust for non-Python languages
    if hasattr(args,"language") and args.language and args.language.lower()!="python":
        return True
    
    # Use Rust for run-all unless python-only is specified
    if command=="run-all":
        python_only = getattr(args, "python_only", False)
        return not python_only
    
    return False


def _run_rust_analyze(args):
    """Delegate analyze command to Rust binary."""
    binary_path=_ensure_rust_binary()
    
    cmd=[str(binary_path),"analyze","--target",args.target]
    
    for inp in args.input:
        cmd.extend(["--input",inp])
    
    cmd.extend(["--repeat",str(args.repeat)])
    cmd.extend(["--timeout",str(args.timeout)])
    cmd.extend(["--output-dir",args.log_dir])
    
    if hasattr(args,"language") and args.language:
        cmd.extend(["--language",args.language])
    
    if hasattr(args,"analysis_mode"):
        cmd.extend(["--analysis-mode",args.analysis_mode])
    
    if args.verbose:
        cmd.append("--verbose")
    
    result=subprocess.run(cmd,check=False)
    return result.returncode


def _run_rust_run_all(args):
    """Delegate run-all command to Rust binary."""
    binary_path=_ensure_rust_binary()
    root_dir=Path(__file__).resolve().parent.parent
    
    cmd=[
        str(binary_path),
        "run-all",
        "--test-dir",
        str(root_dir/"tests"),
        "--generate",
        str(args.generate),
        "--output-dir",
        args.log_dir,
    ]
    
    if hasattr(args,"language") and args.language:
        cmd.extend(["--language",args.language])
    
    result=subprocess.run(cmd,check=False)
    return result.returncode


def _run_rust_list(args):
    """Delegate list command to Rust binary."""
    binary_path=_ensure_rust_binary()
    
    cmd=[str(binary_path),"list"]
    
    if args.detailed:
        cmd.append("--detailed")
    
    result=subprocess.run(cmd,check=False)
    return result.returncode


def main():
    parser=argparse.ArgumentParser(
        prog="graphene",
        description="Multi-language concurrency escape detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  uv run graphene analyze my_module:my_function --input "hello" --repeat 3
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --input "test" --analysis-mode both
  uv run graphene run-all --language python
  uv run graphene run-all --generate 10
  uv run graphene list --detailed
"""
    )
    
    subparsers=parser.add_subparsers(dest="command",help="Command to execute")
    
    # Analyze command
    analyze_parser=subparsers.add_parser("analyze",help="Analyze a function for concurrency escapes")
    analyze_parser.add_argument("target",help="Function target in format: module:function or file.ext:function")
    analyze_parser.add_argument("--input",action="append",default=[],help="Input data for the function (repeatable)")
    analyze_parser.add_argument("--input-file",help="File with one input per line")
    analyze_parser.add_argument("--repeat",type=_validate_positive_int,default=DEFAULT_REPEAT_COUNT,help=f"Repeat each input N times (default: {DEFAULT_REPEAT_COUNT})")
    analyze_parser.add_argument("--generate",type=int,default=0,help="Generate N simple inputs (Python only)")
    analyze_parser.add_argument("--seed",type=int,help="Seed for generated inputs (Python only)")
    analyze_parser.add_argument("--timeout",type=_validate_positive_float,default=DEFAULT_TIMEOUT,help=f"Timeout per execution in seconds (default: {DEFAULT_TIMEOUT})")
    analyze_parser.add_argument("--log-dir",default=DEFAULT_LOG_DIR,help=f"Output directory for reports (default: {DEFAULT_LOG_DIR})")
    analyze_parser.add_argument("--test-name",help="Test session name (Python only)")
    analyze_parser.add_argument("--language",help="Language (python, java, javascript, go, rust). Auto-detected if not specified")
    analyze_parser.add_argument("--analysis-mode",choices=["dynamic","static","both"],default="dynamic",help="Analysis mode: dynamic (runtime), static (compile-time), or both (default: dynamic)")
    analyze_parser.add_argument("--thread-mode",action="store_true",help="Force thread-based execution (Python only)")
    analyze_parser.add_argument("--main-thread-mode",action="store_true",help="Run in main thread (Python only)")
    analyze_parser.add_argument("--process-mode",action="store_true",help="Force process isolation (Python only)")
    analyze_parser.add_argument("--show-ok",action="store_true",help="Show per-attempt OK logs (Python only)")
    analyze_parser.add_argument("--verbose",action="store_true",help="Enable verbose logging")
    
    # Run-all command
    runall_parser=subparsers.add_parser("run-all",help="Run all test suites across languages")
    runall_parser.add_argument("--test-dir",default=DEFAULT_TEST_DIR,help=f"Root test directory (default: {DEFAULT_TEST_DIR})")
    runall_parser.add_argument("--generate",type=int,default=10,help="Number of inputs to generate per test (default: 10)")
    runall_parser.add_argument("--log-dir",default=DEFAULT_LOG_DIR,help=f"Output directory for reports (default: {DEFAULT_LOG_DIR})")
    runall_parser.add_argument("--language",help="Filter by language (python, java, javascript, go, rust)")
    runall_parser.add_argument("--python-only",action="store_true",help="Run only Python tests using native Python harness")
    runall_parser.add_argument("--repeat",type=_validate_positive_int,default=1,help="Repeat each input N times (Python-only mode, default: 1)")
    runall_parser.add_argument("--seed",type=int,help="Seed for generated inputs (Python-only mode)")
    runall_parser.add_argument("--timeout",type=_validate_positive_float,default=DEFAULT_TIMEOUT,help=f"Timeout in seconds (Python-only mode, default: {DEFAULT_TIMEOUT})")
    runall_parser.add_argument("--thread-mode",action="store_true",help="Force thread-based execution (Python-only mode)")
    runall_parser.add_argument("--main-thread-mode",action="store_true",help="Run in main thread (Python-only mode)")
    runall_parser.add_argument("--process-mode",action="store_true",help="Force process isolation (Python-only mode)")
    runall_parser.add_argument("--test-name",help="Test session name (Python-only mode)")
    runall_parser.add_argument("--show-ok",action="store_true",help="Show per-attempt OK logs (Python-only mode)")
    runall_parser.add_argument("--verbose",action="store_true",help="Enable verbose logging")
    
    # List command
    list_parser=subparsers.add_parser("list",help="List available analyzers")
    list_parser.add_argument("--detailed",action="store_true",help="Show detailed analyzer capabilities")
    
    # Help command
    help_parser=subparsers.add_parser("help",help="Show help information")
    help_parser.add_argument("topic",nargs="?",choices=["analyze","run-all","list"],help="Topic to get help for (analyze, run-all, list). Omit for general help")
    
    args=parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Help command
    if args.command=="help":
        topic=getattr(args,"topic",None)
        show_help(topic)
        return 0
    
    # List command always uses Rust binary
    if args.command=="list":
        return _run_rust_list(args)
    
    # Route based on requirements
    if args.command=="analyze":
        if args.thread_mode and args.process_mode:
            parser.error("--thread-mode and --process-mode are mutually exclusive")
        if args.main_thread_mode and args.process_mode:
            parser.error("--main-thread-mode and --process-mode are mutually exclusive")
        if args.main_thread_mode and args.thread_mode:
            parser.error("--main-thread-mode and --thread-mode are mutually exclusive")
        
        # Collect inputs
        inputs=list(args.input or [])
        if args.input_file:
            with open(args.input_file,"r",encoding="utf-8") as f:
                inputs.extend([line.rstrip("\n") for line in f])
        if args.generate:
            inputs.extend(_generate_inputs(args.generate,args.seed))
        if not inputs:
            inputs=[""]
        args.input=inputs
        
        # Delegate to Rust if needed
        if _should_use_rust_binary(args,"analyze"):
            return _run_rust_analyze(args)
        
        # Python-only native execution
        run_label=datetime.now().strftime("run_%Y%m%d_%H%M%S")
        logger=TestingLogger(log_dir=args.log_dir,test_name=args.test_name,show_success=args.show_ok,run_dir=run_label)
        _configure_logger(logger,args.verbose)
        func=_load_function(args.target)
        
        default_thread_mode = os.name == "nt" and not args.process_mode and not args.main_thread_mode
        default_main_thread_mode = os.name == "nt" and not args.process_mode and args.main_thread_mode
        prefer_main_thread=args.main_thread_mode or default_main_thread_mode
        prefer_thread=(args.thread_mode or default_thread_mode) and not prefer_main_thread
        
        _run_tests(func,args.input,args.repeat,args.timeout,logger,prefer_thread=prefer_thread,prefer_main_thread=prefer_main_thread)
        return 0
    
    elif args.command=="run-all":
        if args.thread_mode and args.process_mode:
            parser.error("--thread-mode and --process-mode are mutually exclusive")
        if args.main_thread_mode and args.process_mode:
            parser.error("--main-thread-mode and --process-mode are mutually exclusive")
        if args.main_thread_mode and args.thread_mode:
            parser.error("--main-thread-mode and --thread-mode are mutually exclusive")
        
        # Delegate to Rust unless python-only
        if _should_use_rust_binary(args,"run-all"):
            if args.thread_mode or args.main_thread_mode or args.process_mode:
                print("Warning: thread/process mode flags are ignored in multi-language mode",file=sys.stderr)
            return _run_rust_run_all(args)
        
        # Python-only native execution
        root_dir=Path(__file__).resolve().parent.parent
        tests=_discover_tests(root_dir)
        
        inputs=[]
        if args.generate:
            inputs.extend(_generate_inputs(args.generate,args.seed))
        if not inputs:
            inputs=[""]
        
        run_label=datetime.now().strftime("run_%Y%m%d_%H%M%S")
        default_thread_mode = os.name == "nt" and not args.process_mode and not args.main_thread_mode
        default_main_thread_mode = os.name == "nt" and not args.process_mode and args.main_thread_mode
        
        for target,func,requires_thread,requires_main in tests:
            base_name=args.test_name or "escape_suite"
            test_name=f"{base_name}_{func.__module__.split('.')[-1]}_{func.__name__}"
            logger=TestingLogger(log_dir=args.log_dir,test_name=test_name,show_success=args.show_ok,run_dir=run_label)
            _configure_logger(logger,args.verbose)
            
            prefer_main_thread=args.main_thread_mode or requires_main or default_main_thread_mode
            prefer_thread=(args.thread_mode or requires_thread or default_thread_mode) and not prefer_main_thread
            
            _run_tests(func,inputs,args.repeat,args.timeout,logger,prefer_thread=prefer_thread,prefer_main_thread=prefer_main_thread)
        
        return 0
    
    return 1


if __name__=="__main__":
    sys.exit(main())
