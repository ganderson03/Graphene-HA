#!/usr/bin/env python3
import argparse
import importlib
import importlib.util
import inspect
import logging
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

ROOT_DIR = Path(__file__).resolve().parent.parent

# Input generation patterns (module-level constant)
_INPUT_PATTERNS=[
    "","0","-1","1","true","false","null","undefined","hello","\\x00","\\n","\\t","'","\"",
    "()","[]","{}","../","..\\","${HOME}","$(whoami)","{{7*7}}","%s","A"*1024,"error","exception",
    "1"*100,"test"*50,"async","await","timeout","deadlock","race","concurrent"," "*1000,"\\n"*100,
    "<script>alert(1)</script>","'; DROP TABLE; --","../../../etc/passwd","\\x1b[31m","\\u0000",
]


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


class TestingLogger:
    def __init__(self,log_dir="logs",test_name=None,show_success=False,run_dir=None):
        base_dir=Path(log_dir)
        run_label=run_dir or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        self.log_dir=base_dir/run_label/(test_name or "unnamed_test")
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_name=test_name or f"escape_test_{timestamp}"
        self.log_file=self.log_dir/f"{self.test_name}.log"
        self.details_file=self.log_dir/f"{self.test_name}_details.csv"
        self.vuln_file=self.log_dir/f"{self.test_name}_vulnerabilities.md"
        self.summary_file=self.log_dir/"README.md"
        self._vuln_header_written=False
        self._initialized=False
        self._has_vuln=False
        self.show_success=show_success
        self.logger=logging.getLogger("EscapeTester")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        ch=logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        self.logger.addHandler(ch)

    @staticmethod
    def _format_input_markdown(input_data):
        if not input_data:
            return "(empty)"
        safe_input=input_data.replace("`","\\`")
        return f"`{safe_input}`"

    def _ensure_file_logging(self):
        if self._initialized:
            return
        self.log_dir.mkdir(parents=True,exist_ok=True)
        fh=logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(fh)
        with open(self.details_file,'w',encoding="utf-8") as f:
            f.write("attempt_num,timestamp,input,input_length,output_length,crashed,escape_detected,escape_details,vulnerabilities,execution_time_ms,status\n")
        self._initialized=True
    @staticmethod
    def _format_escape_details(details):
        if not details:
            return ""
        parts=[]
        for item in details.split(";"):
            if item.startswith("thread:"):
                p=item.split(":",2)
                parts.append(f"Thread {p[1]} ({p[2]})" if len(p)==3 else item)
            elif item.startswith("process:"):
                parts.append(f"Process {item.split(':',1)[1]}")
            else:
                parts.append(item)
        return "; ".join(parts)
    @staticmethod
    def _format_status(result,vulnerabilities):
        if result.error == "Timeout exceeded":
            base="TIMEOUT"
        elif result.crashed:
            base="CRASH"
        else:
            base="OK"
        status_parts=[base]
        if getattr(result,"escape_detected",False):
            status_parts.append("ESCAPE")
        if vulnerabilities:
            status_parts.append(f"VULN({len(vulnerabilities)})")
        return " | ".join(status_parts)
    def log_attempt(self,attempt_num,input_data,result,vulnerabilities=None,exec_time_ms=0):
        vulnerabilities=vulnerabilities or []
        escape_detected=getattr(result,"escape_detected",False)
        status=self._format_status(result,vulnerabilities)
        if self.show_success or result.crashed or vulnerabilities or escape_detected:
            self.logger.info(f"[Attempt {attempt_num}] Input: {repr(input_data[:80])} | Status: {status} | Time: {exec_time_ms:.1f}ms")
        if result.crashed:
            self.logger.debug(f"  Crash: {result.anomaly or 'unknown'}, Error: {result.error[:200]}")
        if escape_detected:
            self.logger.warning(f"  Escape: {self._format_escape_details(result.escape_details) or 'details unavailable'}")
        if vulnerabilities:
            self._has_vuln=True
            self._ensure_file_logging()
            for v in vulnerabilities:
                self.logger.warning(f"  VULN: {v.vulnerability_type.upper()} ({v.severity})")
                self._write_vulnerability(attempt_num,input_data,result,v)
            input_escaped=input_data.replace('"','""')
            vuln_str="; ".join([f"{v.vulnerability_type}" for v in vulnerabilities])
            escape_flag=str(escape_detected)
            escape_details=getattr(result,"escape_details","") or ""
            escape_details_escaped=escape_details.replace('"','""')
            csv=f'{attempt_num},{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},"{input_escaped}",{len(input_data)},{len(result.output or "")},{result.crashed},{escape_flag},"{escape_details_escaped}","{vuln_str}",{exec_time_ms:.2f},{status}\n'
            with open(self.details_file,'a',encoding="utf-8") as f:
                f.write(csv)
    def _write_vulnerability(self,attempt_num,input_data,result,vulnerability):
        if not self._vuln_header_written:
            with open(self.vuln_file,"w",encoding="utf-8") as f:
                f.write("# Vulnerability Report\n\n")
                f.write(f"Test: {self.test_name}\n\n")
                f.write("This report describes concurrency escapes detected during execution.\n\n")
            self._vuln_header_written=True
        escape_details=getattr(result,"escape_details","") or ""
        with open(self.vuln_file,"a",encoding="utf-8") as f:
            f.write("---\n\n")
            f.write(f"Attempt: {attempt_num}\n\n")
            f.write(f"Type: {vulnerability.vulnerability_type}\n\n")
            f.write(f"Severity: {vulnerability.severity}\n\n")
            f.write(f"Input: {self._format_input_markdown(input_data)}\n\n")
            f.write("Summary:\n\n")
            f.write("A concurrent worker outlived the test harness, which means execution escaped the expected boundary.\n\n")
            f.write(f"Details: {vulnerability.error_message}\n\n")
            if escape_details:
                f.write(f"Escape Details: {escape_details}\n\n")
            f.write("Impact:\n\n")
            f.write("Escaped threads/processes can keep running after the test completes, causing resource leaks, nondeterministic behavior, or state corruption across runs.\n\n")
            f.write("Suggested Fix:\n\n")
            f.write("Ensure all spawned threads/processes are joined or terminated before returning, or mark threads as daemon only when it is safe to abandon work.\n\n")
    def log_session_start(self,target,inputs,total_runs,timeout):
        self.logger.info("="*70)
        self.logger.info("CONCURRENCY ESCAPE TEST SESSION STARTED")
        self.logger.info(f"Target: {target}")
        self.logger.info(f"Inputs: {len(inputs)} | Total Runs: {total_runs}")
        self.logger.info(f"Timeout: {timeout}s")
        self.logger.info(f"Log: {self.log_file}")
        self.logger.info(f"CSV: {self.details_file}")
        self.logger.info("="*70)
    def log_session_end(self,report):
        self.logger.info("="*70)
        self.logger.info("SESSION COMPLETED")
        self.logger.info(f"Total: {report.total_tests} | Crashes: {report.crashes} | Success: {report.successes} | Escapes: {report.escapes}")
        self.logger.info(f"Crash Rate: {report.crash_rate*100:.2f}% | Vulns: {len(report.vulnerabilities)}")
        self.logger.info("="*70)
        self._write_summary(report)

    def _write_summary(self,report):
        if not self._has_vuln:
            return
        self._ensure_file_logging()
        with open(self.summary_file,"w",encoding="utf-8") as f:
            f.write(f"# {self.test_name}\n\n")
            f.write("This summary highlights concurrency escapes discovered during the test run.\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Total runs: {report.total_tests}\n")
            f.write(f"- Successes: {report.successes}\n")
            f.write(f"- Crashes: {report.crashes}\n")
            f.write(f"- Escapes: {report.escapes}\n")
            f.write(f"- Vulnerabilities: {len(report.vulnerabilities)}\n\n")
            if not report.vulnerabilities:
                f.write("No vulnerabilities were detected in this test.\n")
                return
            f.write("## Vulnerabilities\n\n")
            by_type={}
            for vuln in report.vulnerabilities:
                by_type.setdefault(vuln.vulnerability_type,[]).append(vuln)
            for vuln_type,vulns in by_type.items():
                f.write(f"### {vuln_type}\n\n")
                f.write(f"Count: {len(vulns)}\n\n")
                f.write("What it means:\n\n")
                f.write("A thread or process created by the target continued running after the function returned.\n\n")
                for index,vuln in enumerate(vulns[:3],start=1):
                    f.write(f"#### Example {index}\n\n")
                    f.write(f"- Severity: {vuln.severity}\n")
                    f.write(f"- Input: {self._format_input_markdown(vuln.input)}\n")
                    f.write(f"- Details: {vuln.error_message}\n\n")
                if len(vulns) > 3:
                    f.write(f"...and {len(vulns) - 3} more\n\n")


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
    return [rng.choice(_INPUT_PATTERNS) for _ in range(count)]


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
    analyze_parser.add_argument("--repeat",type=int,default=3,help="Repeat each input N times (default: 3)")
    analyze_parser.add_argument("--generate",type=int,default=0,help="Generate N simple inputs (Python only)")
    analyze_parser.add_argument("--seed",type=int,help="Seed for generated inputs (Python only)")
    analyze_parser.add_argument("--timeout",type=float,default=5.0,help="Timeout per execution in seconds (default: 5.0)")
    analyze_parser.add_argument("--log-dir",default="logs",help="Output directory for reports (default: logs)")
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
    runall_parser.add_argument("--test-dir",default="tests",help="Root test directory (default: tests)")
    runall_parser.add_argument("--generate",type=int,default=10,help="Number of inputs to generate per test (default: 10)")
    runall_parser.add_argument("--log-dir",default="logs",help="Output directory for reports (default: logs)")
    runall_parser.add_argument("--language",help="Filter by language (python, java, javascript, go, rust)")
    runall_parser.add_argument("--python-only",action="store_true",help="Run only Python tests using native Python harness")
    runall_parser.add_argument("--repeat",type=int,default=1,help="Repeat each input N times (Python-only mode, default: 1)")
    runall_parser.add_argument("--seed",type=int,help="Seed for generated inputs (Python-only mode)")
    runall_parser.add_argument("--timeout",type=float,default=5.0,help="Timeout in seconds (Python-only mode, default: 5.0)")
    runall_parser.add_argument("--thread-mode",action="store_true",help="Force thread-based execution (Python-only mode)")
    runall_parser.add_argument("--main-thread-mode",action="store_true",help="Run in main thread (Python-only mode)")
    runall_parser.add_argument("--process-mode",action="store_true",help="Force process isolation (Python-only mode)")
    runall_parser.add_argument("--test-name",help="Test session name (Python-only mode)")
    runall_parser.add_argument("--show-ok",action="store_true",help="Show per-attempt OK logs (Python-only mode)")
    runall_parser.add_argument("--verbose",action="store_true",help="Enable verbose logging")
    
    # List command
    list_parser=subparsers.add_parser("list",help="List available analyzers")
    list_parser.add_argument("--detailed",action="store_true",help="Show detailed analyzer capabilities")
    
    args=parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
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
