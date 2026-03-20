#!/usr/bin/env python3
"""
Static object escape analysis for Python using AST parsing.
Detects variables that escape local scope through various mechanisms.
"""

import ast
import sys
import json
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class EscapeInfo:
    escape_type: str
    line: int
    column: int
    variable_name: str
    reason: str
    confidence: str
    code_snippet: Optional[str] = None


class ObjectEscapeAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST for object escape analysis.
    
    Detects when objects allocated in a function escape local scope through:
    - Return statements
    - Parameter passing
    - Global/module scope assignment
    - Closure capture
    - Heap allocation in containers/structures
    - Concurrency primitives (threads, processes, executors) not properly joined/shutdown
    """
    
    def __init__(self, source_code: str, target_function: str, source_file: str = ""):
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.target_function = target_function
        self.source_file = source_file
        self.escapes: List[EscapeInfo] = []
        self.current_function: Optional[str] = None
        self.local_vars: Set[str] = set()
        self.nonlocal_vars: Set[str] = set()
        self.global_vars: Set[str] = set()
        self.in_target_function = False
        # Track object allocations
        self.allocated_objects: Dict[str, tuple] = {}  # var_name -> (line, col)
        # Track concurrency objects and their join status
        self.concurrency_objects: Dict[str, tuple] = {}  # var_name -> (line, col, type)
        self.joined_objects: Set[str] = set()
        self.join_in_all_paths: Set[str] = set()
        self.join_in_some_paths: Set[str] = set()
        self.reassigned_vars: Set[str] = set()
        # Track imports for cross-file analysis
        self.imports: Dict[str, str] = {}  # alias -> module
        self.import_froms: Dict[str, Tuple[str, str]] = {}  # name -> (module, orig_name)
        # Scan imports first
        self._scan_imports()
        self.join_in_all_paths: Set[str] = set()
        self.join_in_some_paths: Set[str] = set()
        self.reassigned_vars: Set[str] = set()
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        previous_function = self.current_function
        previous_in_target = self.in_target_function
        previous_locals = self.local_vars.copy()
        previous_nonlocals = self.nonlocal_vars.copy()
        previous_globals = self.global_vars.copy()
        previous_concurrency = self.concurrency_objects.copy() if hasattr(self, 'concurrency_objects') else {}
        previous_joined = self.join_in_all_paths.copy() if hasattr(self, 'join_in_all_paths') else set()
        
        self.current_function = node.name
        self.in_target_function = (node.name == self.target_function)
        self.local_vars = set(arg.arg for arg in node.args.args)
        self.nonlocal_vars = set()
        self.global_vars = set()
        self.allocated_objects = {}
        
        if self.in_target_function:
            # Clear concurrency tracking for target function
            self.concurrency_objects = {}
            self.joined_objects = set()
            self.join_in_all_paths = set()
            self.join_in_some_paths = set()
            self.reassigned_vars = set()
            
            # Analyze the function body
            for stmt in node.body:
                self.visit(stmt)
            
            # Check for unjoined concurrency objects
            self._check_unjoined_concurrency()
        else:
            # For non-target functions, still analyze but don't track concurrency
            for stmt in node.body:
                self.visit(stmt)
        
        # Restore context
        self.current_function = previous_function
        self.in_target_function = previous_in_target
        self.local_vars = previous_locals
        self.nonlocal_vars = previous_nonlocals
        self.global_vars = previous_globals
        if previous_concurrency:
            self.concurrency_objects = previous_concurrency
            self.join_in_all_paths = previous_joined
    
    def visit_Return(self, node: ast.Return):
        """Detect variables returned from function."""
        if not self.in_target_function or node.value is None:
            return
        
        # Check if returning a call to function that has escapes
        if isinstance(node.value, ast.Call):
            if self._check_function_call_escapes(node.value):
                self.escapes.append(EscapeInfo(
                    escape_type="return",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name="<return value>",
                    reason=f"Returned value from function with unjoined concurrency",
                    confidence="high",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
                self.generic_visit(node)
                return
        
        # Check if returning a local variable or object
        returned_vars = self._extract_names(node.value)
        for var in returned_vars:
            if var in self.local_vars or var in self.allocated_objects:
                self.escapes.append(EscapeInfo(
                    escape_type="return",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name=var,
                    reason=f"Object '{var}' returned from function",
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
        """Track variable assignments and object allocation."""
        if not self.in_target_function:
            return
        
        # Add assigned variables to local_vars
        for target in node.targets:
            names = self._extract_names(target)
            # Track reassignments
            for name in names:
                if name in self.concurrency_objects:
                    self.reassigned_vars.add(name)
            self.local_vars.update(names)
        
        # Track concurrency object creation
        if isinstance(node.value, ast.Call):
            concurrency_type = self._is_concurrency_call(node.value)
            if concurrency_type:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        self.concurrency_objects[var_name] = (node.lineno, node.col_offset, concurrency_type)
            else:
                # Check if this is a call to an imported function that has escapes
                if self._check_function_call_escapes(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # Mark as return value of function with escapes
                            self.escapes.append(EscapeInfo(
                                escape_type="parameter",
                                line=node.lineno,
                                column=node.col_offset,
                                variable_name=var_name,
                                reason=f"Variable '{var_name}' assigned from function with unjoined concurrency",
                                confidence="high",
                                code_snippet=self._get_code_snippet(node.lineno)
                            ))
        elif isinstance(node.value, ast.ListComp):
            # Check if list comprehension creates concurrency objects
            if isinstance(node.value.elt, ast.Call):
                concurrency_type = self._is_concurrency_call(node.value.elt)
                if concurrency_type:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            self.concurrency_objects[var_name] = (node.lineno, node.col_offset, f"{concurrency_type} list")
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Detect parameter escapes and function calls."""
        if not self.in_target_function:
            return
        
        # Check for variables passed as arguments (parameter escape)
        for arg in node.args:
            escaped_vars = self._extract_names(arg)
            for var in escaped_vars:
                if var in self.local_vars or var in self.allocated_objects:
                    self.escapes.append(EscapeInfo(
                        escape_type="parameter",
                        line=node.lineno,
                        column=node.col_offset,
                        variable_name=var,
                        reason=f"Object '{var}' passed as parameter",
                        confidence="high",
                        code_snippet=self._get_code_snippet(node.lineno)
                    ))
        
        # Check keyword arguments
        for keyword in node.keywords:
            if isinstance(keyword.value, ast.Name):
                var = keyword.value.id
                if var in self.local_vars or var in self.allocated_objects:
                    self.escapes.append(EscapeInfo(
                        escape_type="parameter",
                        line=node.lineno,
                        column=node.col_offset,
                        variable_name=var,
                        reason=f"Object '{var}' passed as keyword argument",
                        confidence="high",
                        code_snippet=self._get_code_snippet(node.lineno)
                    ))
        
        self.generic_visit(node)
    
    def visit_Lambda(self, node: ast.Lambda):
        """Detect closures capturing local objects."""
        if not self.in_target_function:
            return
        
        # Variables used in lambda that are defined in outer scope escape
        used_vars = self._find_used_variables(node.body)
        lambda_args = set(arg.arg for arg in node.args.args)
        
        for var in used_vars:
            if (var in self.local_vars or var in self.allocated_objects) and var not in lambda_args:
                self.escapes.append(EscapeInfo(
                    escape_type="closure",
                    line=node.lineno,
                    column=node.col_offset,
                    variable_name=var,
                    reason=f"Object '{var}' captured in lambda/closure",
                    confidence="high",
                    code_snippet=self._get_code_snippet(node.lineno)
                ))
        
        self.generic_visit(node)
    
    def _extract_names(self, node: ast.AST) -> List[str]:
        """Extract variable names from an AST node."""
        names = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
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
    
    def visit_For(self, node: ast.For):
        """Track for loops that iterate over concurrency objects."""
        if not self.in_target_function:
            self.generic_visit(node)
            return
        
        # Check if iterating over a known concurrency object list
        if isinstance(node.iter, ast.Name):
            iter_var = node.iter.id
            
            # Check if .join() is called in this loop
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute):
                        if stmt.value.func.attr == 'join':
                            # Mark the iterated list as joined in all paths
                            self.join_in_all_paths.add(iter_var)
        
        self.generic_visit(node)
    
    def visit_Expr(self, node: ast.Expr):
        """Handle expression statements (method calls that are statements)."""
        if not self.in_target_function or not isinstance(node.value, ast.Call):
            self.generic_visit(node)
            return
        
        call = node.value
        
        # Check for .join(), .close(), .shutdown() calls
        if isinstance(call.func, ast.Attribute):
            attr = call.func.attr
            
            if attr == 'join':
                if isinstance(call.func.value, ast.Name):
                    var_name = call.func.value.id
                    self.join_in_all_paths.add(var_name)
            
            elif attr in ['close', 'shutdown', 'terminate']:
                if isinstance(call.func.value, ast.Name):
                    var_name = call.func.value.id
                    self.join_in_all_paths.add(var_name)
        
        self.generic_visit(node)
    
    def _is_concurrency_call(self, node: ast.Call) -> Optional[str]:
        """Check if a Call node creates a concurrency object. Returns the type if so."""
        try:
            call_str = ast.unparse(node.func) if hasattr(ast, 'unparse') else str(node.func)
        except:
            return None
        
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
    
    def _scan_imports(self):
        """Scan the source code for import statements."""
        try:
            tree = ast.parse(self.source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        self.imports[name] = alias.name
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        self.import_froms[name] = (module, alias.name)
        except:
            pass
    
    def _resolve_imported_function(self, func_ref: str) -> Optional[str]:
        """Try to resolve an imported function to its source file."""
        # Check if it's a module.function reference
        if '.' in func_ref:
            module_alias, func_name = func_ref.split('.', 1)
            if module_alias in self.imports:
                module_path = self.imports[module_alias]
                return self._find_imported_module(module_path, func_name)
        return None
    
    def _find_imported_module(self, module_name: str, func_name: str, call_node: Optional[ast.Call] = None) -> Optional[str]:
        """Try to find and analyze an imported module.
        
        Args:
            module_name: Name of the module to import
            func_name: Function to analyze
            call_node: Optional AST node of the call to check for daemon parameter
        """
        if not self.source_file:
            return None
        
        source_dir = Path(self.source_file).parent
        
        # Try different module path variants
        possible_paths = [
            source_dir / f"{module_name}.py",
            source_dir / module_name / "__init__.py",
            Path(module_name.replace('.', '/') + '.py'),
        ]
        
        for path in possible_paths:
            try:
                if path.exists():
                    with open(path, 'r') as f:
                        imported_code = f.read()
                    
                    # Analyze the imported function
                    temp_analyzer = ObjectEscapeAnalyzer(imported_code, func_name, str(path))
                    temp_analyzer.visit(ast.parse(imported_code))
                    
                    # Check if daemon=True was passed - if so, the escape is acceptable
                    if call_node:
                        for keyword in call_node.keywords:
                            if keyword.arg == 'daemon':
                                # Check if value is True
                                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                    return None  # Daemon thread is safe, no escape
                                elif isinstance(keyword.value, ast.NameConstant) and keyword.value.value is True:
                                    return None  # Daemon thread is safe, no escape
                    
                    # If the imported function has escapes, mark our call as problematic
                    if temp_analyzer.escapes:
                        return f"{path}:{func_name}"
            except:
                continue
        
        return None
    
    def _check_function_call_escapes(self, node: ast.Call) -> bool:
        """Check if a function call might have escapes in its implementation."""
        if isinstance(node.func, ast.Attribute):
            # Handle attribute calls like h.spawn_worker()
            if isinstance(node.func.value, ast.Name):
                module_alias = node.func.value.id
                func_name = node.func.attr
                
                # Check if this is an imported module
                if module_alias in self.imports:
                    module_path = self.imports[module_alias]
                    # Pass the call node so we can check for daemon parameter
                    result = self._find_imported_module(module_path, func_name, node)
                    return result is not None
        
        return False
    
    def _check_unjoined_concurrency(self):
        """Check for concurrency objects that were created but not joined in ALL code paths."""
        for var_name, (line, col, obj_type) in self.concurrency_objects.items():
            # Only report if join was NOT called in all paths and variable wasn't reassigned
            if var_name not in self.join_in_all_paths and var_name not in self.reassigned_vars:
                confidence = "high"
                reason = f"{obj_type} '{var_name}' created but not properly joined/closed"
                
                self.escapes.append(EscapeInfo(
                    escape_type="concurrency",
                    line=line,
                    column=col,
                    variable_name=var_name,
                    reason=reason,
                    confidence=confidence,
                    code_snippet=self._get_code_snippet(line)
                ))


def analyze_file(file_path: str, function_name: str) -> Dict[str, Any]:
    """Analyze a Python file for object escape patterns in a specific function."""
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
        analyzer = ObjectEscapeAnalyzer(source_code, function_name, file_path)
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
            "error": "Usage: static_analyzer.py <file_path> <function_name>"
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
        
        result = analyze_file(file_path, function_name)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "escapes": [],
            "success": False,
            "error": f"Error: {type(e).__name__}: {str(e)}"
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
