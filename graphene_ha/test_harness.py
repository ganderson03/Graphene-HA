import os
import pickle
import queue
import time
import multiprocessing
import asyncio
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TestResult:
 input_data:str
 success:bool
 crashed:bool
 output:str
 error:str
 return_code:int
 anomaly:bool=False
 escape_detected:bool=False
 escape_details:str=""

def _get_child_processes_from_proc(parent_pid=None):
 """Get child processes using /proc filesystem (Linux only)"""
 try:
  if parent_pid is None:
   parent_pid = os.getpid()
  
  # Look for child processes in /proc
  children = []
  for status_file in Path("/proc").glob("*/status"):
   try:
    with open(status_file) as f:
     content = f.read()
     if f"PPid:\t{parent_pid}" in content:
      pid = int(status_file.parent.name)
      children.append(pid)
   except (FileNotFoundError, ValueError, PermissionError):
    pass
  return children
 except Exception:
  return []

def _collect_escape_details(baseline_thread_ids, baseline_children):
 import threading
 import multiprocessing as mp
 
 # Collect thread escapes
 current_threads = threading.enumerate()
 current_thread_ids = {thr.ident for thr in current_threads}
 escape_thread_ids = current_thread_ids - baseline_thread_ids
 escape_threads = [thr for thr in current_threads if thr.ident in escape_thread_ids and thr.is_alive()]
 escape_details = [f"thread:{thr.name}:{'daemon' if thr.daemon else 'nondaemon'}" for thr in escape_threads]
 
 # Collect process escapes (conservative detection)
 escaped_child_pids = set()
 
 # Layer 1: multiprocessing.active_children() - most reliable
 current_children = {child.pid for child in mp.active_children()}
 new_processes = current_children - baseline_children
 
 # Only consider processes that are actively tracked by multiprocessing
 # This avoids false positives from system processes
 for pid in new_processes:
  try:
   # Verify it's actually a child process we created
   if os.path.exists(f"/proc/{pid}/status"):
    with open(f"/proc/{pid}/status") as f:
     content = f.read()
     # Extract process name
     for line in content.split('\n'):
      if line.startswith("Name:"):
       name = line.split(":", 1)[1].strip()
       escape_details.append(f"process:{pid}:{name}")
       escaped_child_pids.add(pid)
       break
  except Exception:
   pass
 
 # Layer 2: /proc filesystem detection (only for spawn processes we might have missed)
 if os.path.exists("/proc") and not escaped_child_pids:
  try:
   proc_children = _get_child_processes_from_proc()
   # Only include processes that are direct children and not in baseline
   for pid in proc_children:
    if pid not in baseline_children and pid not in escaped_child_pids:
     try:
      # Double-check this is actually a Python child process
      if os.path.exists(f"/proc/{pid}/status"):
       with open(f"/proc/{pid}/status") as f:
        content = f.read()
        for line in content.split('\n'):
         if line.startswith("Name:"):
          name = line.split(":", 1)[1].strip()
          # Only add if it looks like a process we created (avoid system processes)
          if name not in ["systemd", "bash", "sh", "grep", "ps"]:
           escape_details.append(f"process:{pid}:{name}")
           escaped_child_pids.add(pid)
          break
     except Exception:
      pass
  except Exception:
   pass
 
 # Detect asyncio task escapes
 try:
  if sys.version_info >= (3, 7):
   try:
    loop = asyncio.get_running_loop()
    all_tasks = asyncio.all_tasks(loop)
    pending_tasks = [task for task in all_tasks if not task.done()]
    for task in pending_tasks:
     coro = task.get_coro()
     escape_details.append(f"asyncio_task:{coro.__name__}:pending")
   except RuntimeError:
    # No running event loop
    pass
 except Exception:
  pass
 
 return bool(escape_details), ";".join(escape_details)

def _function_worker(func,input_data,fixed_kwargs,result_queue):
 import threading
 import multiprocessing as mp
 baseline_threads={thr.ident for thr in threading.enumerate()}
 baseline_children={child.pid for child in mp.active_children()}
 try:
  output=str(func(input_data,**fixed_kwargs));error="";crashed=False
 except Exception as e:
  output="";error=f"{type(e).__name__}: {str(e)}";crashed=True
 time.sleep(0.5)  # Increased wait for child processes to initialize
 escape_detected,escape_details=_collect_escape_details(baseline_threads,baseline_children)
 result_queue.put({"output":output,"error":error,"crashed":crashed,"escape_detected":escape_detected,"escape_details":escape_details})
 result_queue.close()
 result_queue.join_thread()
 os._exit(0)


class PythonFunctionTestHarness:
 def __init__(self, func, timeout=5.0, prefer_thread=False, prefer_main_thread=False, **fixed_kwargs):
  self.func=func
  self.timeout=timeout
  self.prefer_thread=prefer_thread
  self.prefer_main_thread=prefer_main_thread
  self.fixed_kwargs=fixed_kwargs
 def run_test(self,input_data):
  if self.prefer_main_thread:
   return self._run_in_main_thread(input_data)
  if self.prefer_thread:
   return self._run_in_thread(input_data)
  if self._can_pickle(self.func):
   return self._run_in_process(input_data)
  return self._run_in_thread(input_data)
 def _can_pickle(self,func):
  try:
   pickle.dumps(func)
   return True
  except Exception:
   return False
 def _run_in_process(self,input_data):
  baseline_children={child.pid for child in multiprocessing.active_children()}
  ctx=multiprocessing.get_context("spawn")
  result_queue=ctx.Queue()
  proc=ctx.Process(target=_function_worker,args=(self.func,input_data,self.fixed_kwargs,result_queue))
  proc.start()
  proc.join(timeout=self.timeout)
  if proc.is_alive():
   proc.terminate();proc.join()
   time.sleep(0.2)  # Wait for process cleanup
   escape_detected,escape_details=_collect_escape_details(set(),baseline_children)
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error=f"Process timeout after {self.timeout}s (PID: {proc.pid})",return_code=-1,anomaly=True,escape_detected=escape_detected,escape_details=escape_details or "process_timeout")
  time.sleep(0.5)  # Increased wait for grandchild processes to initialize
  try:
   payload=result_queue.get_nowait()
  except queue.Empty:
   escape_detected,escape_details=_collect_escape_details(set(),baseline_children)
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error=f"Child process did not return result (timeout: {self.timeout}s, PID: {proc.pid})",return_code=-1,anomaly=True,escape_detected=escape_detected,escape_details=escape_details)
  if payload.get("crashed"):
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error=payload.get("error",""),return_code=-1,escape_detected=payload.get("escape_detected",False),escape_details=payload.get("escape_details",""))
  return TestResult(input_data=input_data,success=True,crashed=False,output=payload.get("output",""),error="",return_code=0,escape_detected=payload.get("escape_detected",False),escape_details=payload.get("escape_details",""))
 def _run_in_thread(self,input_data):
  import threading
  r={"result":None,"error":None,"completed":False}
  baseline_threads={thr.ident for thr in threading.enumerate()}
  baseline_children={child.pid for child in multiprocessing.active_children()}
  def run_with_timeout():
   try:
    r["result"]=str(self.func(input_data,**self.fixed_kwargs));r["completed"]=True
   except Exception as e:
    r["error"]=f"{type(e).__name__}: {str(e)}";r["completed"]=True
  try:
   t=threading.Thread(target=run_with_timeout,daemon=True);t.start();t.join(timeout=self.timeout)
   if not r["completed"]:
    time.sleep(0.1)
    escape_detected,escape_details=_collect_escape_details(baseline_threads,baseline_children)
    return TestResult(input_data=input_data,success=False,crashed=True,output="",error=f"Thread timeout after {self.timeout}s (TID: {t.ident})",return_code=-1,anomaly=True,escape_detected=escape_detected,escape_details=escape_details or "function_timeout")
   time.sleep(0.2)  # Increased wait for child process initialization
   escape_detected,escape_details=_collect_escape_details(baseline_threads,baseline_children)
   if r["error"]:
    return TestResult(input_data=input_data,success=False,crashed=True,output="",error=r["error"],return_code=-1,escape_detected=escape_detected,escape_details=escape_details)
   return TestResult(input_data=input_data,success=True,crashed=False,output=r["result"],error="",return_code=0,escape_detected=escape_detected,escape_details=escape_details)
  except Exception as e:
   import traceback;return TestResult(input_data=input_data,success=False,crashed=True,output="",error=f"{type(e).__name__}: {str(e)} [thread execution error]",return_code=-1)

 def _run_in_main_thread(self,input_data):
  import threading
  start=time.time()
  baseline_threads={thr.ident for thr in threading.enumerate()}
  baseline_children={child.pid for child in multiprocessing.active_children()}
  try:
   output=str(self.func(input_data,**self.fixed_kwargs))
   error=""
   crashed=False
  except Exception as e:
   output=""
   error=f"{type(e).__name__}: {str(e)}"
   crashed=True
  elapsed=time.time()-start
  time.sleep(0.5)  # Increased wait for child process initialization
  escape_detected,escape_details=_collect_escape_details(baseline_threads,baseline_children)
  if elapsed > self.timeout:
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error="Timeout exceeded",return_code=-1,anomaly=True,escape_detected=escape_detected,escape_details=escape_details or "main_thread_timeout")
  if crashed:
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error=error,return_code=-1,escape_detected=escape_detected,escape_details=escape_details)
  return TestResult(input_data=input_data,success=True,crashed=False,output=output,error="",return_code=0,escape_detected=escape_detected,escape_details=escape_details)
