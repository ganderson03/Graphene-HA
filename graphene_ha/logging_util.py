"""Logging and test reporting module."""

import logging
from datetime import datetime
from pathlib import Path


class TestingLogger:
    def __init__(self,log_dir="logs",test_name=None,show_success=False,run_dir=None):
        base_dir=Path(log_dir).resolve()
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
