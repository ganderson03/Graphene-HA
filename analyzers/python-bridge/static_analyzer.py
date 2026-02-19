#!/usr/bin/env python3
"""
Static escape analysis for Python using AST parsing.
Detects variables that escape local scope through various mechanisms.
"""

import ast
import sys
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class EscapeInfo:
    escape_type: str
    line: int
    column: int
    variable_name: str
    reason: str
    confidence: str
    code_snippet: Optional[str] = None


class EscapeAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST for variable escapes."""
    
    def __init__(self, source_code: str, target_function: str):
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.target_function = target_function
        self.escapes: List[EscapeInfo] = []
        self.current_function = None
        self.local_vars = set()
        self.nonlocal_vars = set()
        self.global_vars = set()
        self.in_target_function = False
        # Track concurrency objects and whether they're joined
        self.concurrency_objects = {}  # var_name -> (line, col, type)
        self.joined_objects = set()  # var_names that have been joined
        # Track control flow for join/cleanup in all paths
        self.join_in_all_paths = set()  # var_names where join is called in ALL code paths
        self.join_in_some_paths = set()  # var_names where join is called in SOME code paths
        # Track variable reassignments
        self.reassigned_vars = set()  # var_names that are reassigned after creation
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        previous_function = self.current_function
        previous_in_target = self.in_target_function
        previous_locals = self.local_vars.copy()
        previous_nonlocals = self.nonlocal_vars.copy()
        previous_globals = self.global_vars.copy()
        
        self.current_function = node.name
        self.in_target_function = (node.name == self.target_function)
        self.local_vars = set(arg.arg for arg in node.args.args)
        self.nonlocal_vars = set()
        self.global_vars = set()
        
        if self.in_target_function:
            # Clear concurrency tracking for target function
            self.concurrency_objects = {}
            self.joined_objects = set()
            
            # Analyze the function body
            for stmt in node.body:
                self.visit(stmt)
            
            # Check for unjoined concurrency objects
            self._check_unjoined_concurrency()
        
        # Restore context
        self.current_function = previous_function
        self.in_target_function = previous_in_target
        self.local_vars = previous_locals
        self.nonlocal_vars = previous_nonlocals
        self.global_vars = previous_globals
    
    def visit_Return(self, node: ast.Return):
        """Detect variables returned from function."""
        if not self.in_target_function or node.value is None:
            return
        
        # Check if returning a local variable or object
        returned_vars = self._extract_names(node.value)
        for var in returned_vars:
            if var in self.local_vars:
                self.escapes.append(EscapeInfo(
                    escape_type="return",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name=var,
                    reason=f"Variable '{var}' returned from function",
                    confidence="high",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
        
        self.generic_visit(node)
    
    def visit_Global(self, node: ast.Global):
        """Track global declarations."""
        if self.in_target_function:
            self.global_vars.update(node.names)
            for name in node.names:
                self.escapes.append(EscapeInfo(
                    escape_type="global",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name=name,
                    reason=f"Variable '{name}' declared as global",
                    confidence="high",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
    
    def visit_Nonlocal(self, node: ast.Nonlocal):
        """Track nonlocal declarations."""
        if self.in_target_function:
            self.nonlocal_vars.update(node.names)
            for name in node.names:
                self.escapes.append(EscapeInfo(
                    escape_type="closure",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name=name,
                    reason=f"Variable '{name}' captured from outer scope",
                    confidence="high",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments."""
        if not self.in_target_function:
            return
        
        # Add assigned variables to local_vars
        for target in node.targets:
            names = self._extract_names(target)
            # Track reassignments (variable reassigned after initial creation)
            for name in names:
                if name in self.concurrency_objects:
                    self.reassigned_vars.add(name)
            self.local_vars.update(names)
            
            # Check if assigning to a global/module attribute
            if isinstance(target, ast.Attribute) or isinstance(target, ast.Subscript):
                # This is likely a global escape
                target_str = ast.unparse(target) if hasattr(ast, 'unparse') else 'unknown'
                if isinstance(node.value, ast.Call):
                    concurrency_type = self._is_concurrency_call(node.value)
                    if concurrency_type:
                        self.escapes.append(EscapeInfo(
                            escape_type="global",
                            line=node.lineno,
                            column=node.col_offset,
                            variable_name=target_str,
                            reason=f"{concurrency_type} assigned to global/attribute {target_str}",
                            confidence="high",
                            code_snippet=self._get_code_snippet(node.lineno)
                        ))
        
        # Track concurrency object creation
        if isinstance(node.value, ast.Call):
            concurrency_type = self._is_concurrency_call(node.value)
            if concurrency_type:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        self.concurrency_objects[var_name] = (node.lineno, node.col_offset, concurrency_type)
        elif isinstance(node.value, ast.ListComp):
            # Check if list comprehension creates concurrency objects
            if isinstance(node.value.elt, ast.Call):
                concurrency_type = self._is_concurrency_call(node.value.elt)
                if concurrency_type:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # Track as a list of concurrency objects
                            self.concurrency_objects[var_name] = (node.lineno, node.col_offset, f"{concurrency_type} list")
        
        # Check for heap allocations (lists, dicts, objects) - but reduce noise
        # Only report if it's a complex object, not simple containers
        if isinstance(node.value, ast.Call):
            call_str = ast.unparse(node.value.func) if hasattr(ast, 'unparse') else str(node.value.func)
            # Skip common types that don't usually escape in harmful ways
            if not any(t in call_str for t in ['list', 'dict', 'set', 'tuple', 'str', 'int', 'float']):
                # Only report heap allocation if it's not a concurrency object (already tracked)
                if not self._is_concurrency_call(node.value):
                    for target in node.targets:
                        names = self._extract_names(target)
                        for name in names:
                            self.escapes.append(EscapeInfo(
                                escape_type="heap",
                                line=node.lineno,
                                column=node.col_offset,
                                variable_name=name,
                                reason=f"Variable '{name}' assigned heap-allocated object",
                                confidence="low",
                                code_snippet=self._get_code_snippet(node.lineno)
                            ))
        
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """Track for loops that iterate over concurrency objects."""
        if not self.in_target_function:
            return
        
        # Check if iterating over a known concurrency object list
        if isinstance(node.iter, ast.Name):
            iter_var = node.iter.id
            
            # Check if .join() is called in this loop
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute):
                        if stmt.value.func.attr == 'join':
                            # Mark the iterated list as joined in all paths (it's in a for loop)
                            self.join_in_all_paths.add(iter_var)
            
            if iter_var in self.concurrency_objects and iter_var not in self.join_in_all_paths:
                # Check if .start() is called in the loop
                has_start = False
                for stmt in node.body:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        if isinstance(stmt.value.func, ast.Attribute):
                            if stmt.value.func.attr == 'start':
                                has_start = True
                                break
                
                # If threads are started, mark as needs checking (will be checked at end of function)
                # We don't report immediately because join might come in a later loop
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Detect concurrency primitives and parameter escapes."""
        if not self.in_target_function:
            return
        
        # Check for .join() calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'join':
                if isinstance(node.func.value, ast.Name):
                    var_name = node.func.value.id
                    self.join_in_all_paths.add(var_name)
            
            # Check for .close() or .shutdown() on pools/executors
            elif node.func.attr in ['close', 'shutdown', 'terminate']:
                if isinstance(node.func.value, ast.Name):
                    var_name = node.func.value.id
                    self.join_in_all_paths.add(var_name)
            
            # Check for Pool methods without proper cleanup
            elif node.func.attr in ['apply_async', 'map_async', 'starmap_async']:
                if isinstance(node.func.value, ast.Name):
                    pool_var = node.func.value.id
                    if pool_var in self.concurrency_objects and pool_var not in self.join_in_all_paths:
                        self.escapes.append(EscapeInfo(
                            escape_type="concurrency",
                            line=node.lineno,
                            column=node.col_offset,
                            variable_name=pool_var,
                            reason=f"Pool async method called without shutdown() in all paths",
                            confidence="medium",
                            code_snippet=self._get_code_snippet(node.lineno)
                        ))
        
        # Check for variables passed as arguments (parameter escape) - reduce noise
        # Only report for concurrency objects that are not being joined
        for arg in node.args:
            escaped_vars = self._extract_names(arg)
            for var in escaped_vars:
                if var in self.concurrency_objects and var not in self.join_in_all_paths:
                    # Don't report if this is passing to a cleanup function
                    func_name = ast.unparse(node.func) if hasattr(ast, 'unparse') else ''
                    if not any(cleanup in func_name for cleanup in ['join', 'wait', 'close', 'shutdown']):
                        self.escapes.append(EscapeInfo(
                            escape_type="parameter",
                            line=node.lineno,
                            column=node.col_offset,
                            variable_name=var,
                            reason=f"Concurrency object '{var}' passed without documented join",
                            confidence="medium",
                            code_snippet=self._get_code_snippet(node.lineno)
                        ))
        
        self.generic_visit(node)
    
    def visit_Lambda(self, node: ast.Lambda):
        """Detect closures."""
        if not self.in_target_function:
            return
        
        # Variables used in lambda that are defined in outer scope escape
        used_vars = self._find_used_variables(node.body)
        lambda_args = set(arg.arg for arg in node.args.args)
        
        for var in used_vars:
            if var in self.local_vars and var not in lambda_args:
                self.escapes.append(EscapeInfo(
                    escape_type="closure",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name=var,
                    reason=f"Variable '{var}' captured in lambda/closure",
                    confidence="high",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
        
        self.generic_visit(node)
    
    def _is_concurrency_call(self, node: ast.Call) -> Optional[str]:
        """Check if a Call node creates a concurrency object. Returns the type if so."""
        call_str = ast.unparse(node.func) if hasattr(ast, 'unparse') else str(node.func)
        
        concurrency_patterns = {
            'Thread': 'Thread',
            'threading.Thread': 'Thread',
            'Timer': 'Timer',
            'threading.Timer': 'Timer',
            'Process': 'Process',
            'multiprocessing.Process': 'Process',
            'mp.Process': 'Process',
            'Pool': 'Pool',
            'multiprocessing.Pool': 'Pool',
            'mp.Pool': 'Pool',
            'ThreadPoolExecutor': 'ThreadPoolExecutor',
            'ProcessPoolExecutor': 'ProcessPoolExecutor',
        }
        
        for pattern, obj_type in concurrency_patterns.items():
            if pattern in call_str:
                return obj_type
        
        return None
    
    def _check_unjoined_concurrency(self):
        """Check for concurrency objects that were created but not joined in ALL code paths."""
        for var_name, (line, col, obj_type) in self.concurrency_objects.items():
            # Only report if join was NOT called in all paths
            if var_name not in self.join_in_all_paths and var_name not in self.reassigned_vars:
                # High confidence if join is in some paths (incomplete cleanup)
                # Medium confidence if join is not tracked (may be cleaned up elsewhere)
                if var_name in self.join_in_some_paths:
                    confidence = "high"
                    reason = f"{obj_type} '{var_name}' not joined in all code paths"
                else:
                    confidence = "high"
                    reason = f"{obj_type} '{var_name}' created but not visibly joined/closed"
                
                self.escapes.append(EscapeInfo(
                    escape_type="concurrency",
                    line=line,
                    column=col,
                    variable_name=var_name,
                    reason=reason,
                    confidence=confidence,
                    code_snippet=self._get_code_snippet(line)
                ))
    
    def _extract_names(self, node: ast.AST) -> List[str]:
        """Extract variable names from an AST node."""
        names = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Tuple) or isinstance(node, ast.List):
            for elt in node.elts:
                names.extend(self._extract_names(elt))
        elif isinstance(node, ast.Attribute):
            names.extend(self._extract_names(node.value))
        return names
    
    def _find_used_variables(self, node: ast.AST) -> set:
        """Find all variables used in an AST subtree."""
        used = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                used.add(child.id)
        return used
    
    def _get_code_snippet(self, line: int) -> Optional[str]:
        """Get code snippet for a given line."""
        if 0 < line <= len(self.source_lines):
            return self.source_lines[line - 1].strip()
        return None


def analyze_file(file_path: str, function_name: str) -> Dict[str, Any]:
    """Analyze a Python file for escape patterns in a specific function."""
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        return {"escapes": [], "success": False, "error": f"File not found: {file_path}"}
    except IOError as e:
        return {"escapes": [], "success": False, "error": f"Cannot read file: {str(e)}"}
    except Exception as e:
        return {"escapes": [], "success": False, "error": f"File error: {type(e).__name__}: {str(e)}"}
    
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        return {"escapes": [], "success": False, "error": f"Syntax error at line {e.lineno}: {str(e)}"}
    except Exception as e:
        return {"escapes": [], "success": False, "error": f"Parse error: {type(e).__name__}: {str(e)}"}
    
    try:
        analyzer = EscapeAnalyzer(source_code, function_name)
        analyzer.visit(tree)
        return {
            "target_function": function_name,
            "escapes": [asdict(e) for e in analyzer.escapes],
            "success": True
        }
    except Exception as e:
        return {
            "escapes": [],
            "success": False,
            "error": f"Analysis failed: {type(e).__name__}: {str(e)}"
        }


def main():
    if len(sys.argv) != 3:
        print(json.dumps({
            "escapes": [],
            "success": False,
            "error": "Usage: static_analyzer.py <file_path> <function_name> (got {} args)".format(len(sys.argv) - 1)
        }))
        sys.exit(1)
    
    file_path = sys.argv[1]
    function_name = sys.argv[2]
    
    try:
        from pathlib import Path
        if not Path(file_path).exists():
            print(json.dumps({
                "escapes": [],
                "success": False,
                "error": f"File not found: {file_path}"
            }))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "escapes": [],
            "success": False,
            "error": f"Cannot access file: {str(e)}"
        }))
        sys.exit(1)
    
    result = analyze_file(file_path, function_name)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
