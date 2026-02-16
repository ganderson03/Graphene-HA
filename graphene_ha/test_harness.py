import os
import pickle
import queue
import time
import multiprocessing
from dataclasses import dataclass

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

def _collect_escape_details(baseline_thread_ids,baseline_children):
 import threading
 import multiprocessing as mp
 current_threads=threading.enumerate()
 current_thread_ids={thr.ident for thr in current_threads}
 escape_thread_ids=current_thread_ids-baseline_thread_ids
 escape_threads=[thr for thr in current_threads if thr.ident in escape_thread_ids and thr.is_alive()]
 escape_details=[f"thread:{thr.name}:{'daemon' if thr.daemon else 'nondaemon'}" for thr in escape_threads]
 escape_details.extend(f"process:{child.pid}" for child in mp.active_children() if child.pid not in baseline_children)
 return bool(escape_details),";".join(escape_details)

def _function_worker(func,input_data,fixed_kwargs,result_queue):
 import threading
 import multiprocessing as mp
 baseline_threads={thr.ident for thr in threading.enumerate()}
 try:
  output=str(func(input_data,**fixed_kwargs));error="";crashed=False
 except Exception as e:
  output="";error=f"{type(e).__name__}: {str(e)}";crashed=True
 time.sleep(0.1)
 escape_detected,escape_details=_collect_escape_details(baseline_threads,{child.pid for child in mp.active_children()})
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
  ctx=multiprocessing.get_context("spawn")
  result_queue=ctx.Queue()
  proc=ctx.Process(target=_function_worker,args=(self.func,input_data,self.fixed_kwargs,result_queue))
  proc.start()
  proc.join(timeout=self.timeout)
  if proc.is_alive():
   proc.terminate();proc.join()
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error="Timeout exceeded",return_code=-1,anomaly=True)
  try:
   payload=result_queue.get_nowait()
  except queue.Empty:
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error="No result from child process",return_code=-1,anomaly=True)
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
    return TestResult(input_data=input_data,success=False,crashed=True,output="",error="Timeout exceeded",return_code=-1,anomaly=True,escape_detected=escape_detected,escape_details=escape_details or "function_timeout")
   time.sleep(0.1)
   escape_detected,escape_details=_collect_escape_details(baseline_threads,baseline_children)
   if r["error"]:
    return TestResult(input_data=input_data,success=False,crashed=True,output="",error=r["error"],return_code=-1,escape_detected=escape_detected,escape_details=escape_details)
   return TestResult(input_data=input_data,success=True,crashed=False,output=r["result"],error="",return_code=0,escape_detected=escape_detected,escape_details=escape_details)
  except Exception as e:
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error=f"{type(e).__name__}: {str(e)}",return_code=-1)

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
  time.sleep(0.1)
  escape_detected,escape_details=_collect_escape_details(baseline_threads,baseline_children)
  if elapsed > self.timeout:
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error="Timeout exceeded",return_code=-1,anomaly=True,escape_detected=escape_detected,escape_details=escape_details or "main_thread_timeout")
  if crashed:
   return TestResult(input_data=input_data,success=False,crashed=True,output="",error=error,return_code=-1,escape_detected=escape_detected,escape_details=escape_details)
  return TestResult(input_data=input_data,success=True,crashed=False,output=output,error="",return_code=0,escape_detected=escape_detected,escape_details=escape_details)
