#!/usr/bin/env node
/**
 * JavaScript/Node.js Static Escape Analyzer
 * Detects concurrency escapes in JavaScript/Node.js code
 */

const fs = require('fs');

const RETAINER_NAME_PATTERN = /(retained|cache|audit|handler|handlers|registry|store)/i;

function extractIdentifiers(expression) {
    return expression.match(/[A-Za-z_$][\w$]*/g) || [];
}

function looksLikeContainerInitializer(rhs) {
    const normalized = rhs.trim();
    return (
        normalized.startsWith('new Map(')
        || normalized.startsWith('new Set(')
        || normalized.startsWith('new WeakMap(')
        || normalized.startsWith('new WeakSet(')
        || normalized === '[]'
        || normalized.startsWith('[')
        || normalized.startsWith('new Array(')
    );
}

function looksLikeObjectInitializer(rhs) {
    const normalized = rhs.trim();
    return (
        normalized.startsWith('{')
        || normalized.startsWith('new Map(')
        || normalized.startsWith('new Set(')
        || normalized.startsWith('new WeakMap(')
        || normalized.startsWith('new WeakSet(')
        || normalized.startsWith('new Object(')
        || normalized.startsWith('new Array(')
        || normalized === '[]'
        || normalized.startsWith('[')
    );
}

function collectModuleRetainers(lines) {
    const retainers = new Set();
    for (const line of lines) {
        const trimmed = line.trim();
        const match = trimmed.match(/^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(.+?);?$/);
        if (!match) {
            continue;
        }
        const name = match[1];
        const rhs = match[2];

        if (RETAINER_NAME_PATTERN.test(name) && looksLikeContainerInitializer(rhs)) {
            retainers.add(name);
        }
    }
    return retainers;
}

function isRetainerContainer(containerName, moduleRetainers) {
    return moduleRetainers.has(containerName) || RETAINER_NAME_PATTERN.test(containerName);
}

function expandDependencies(varName, objectDependencies, output, visited = new Set()) {
    if (visited.has(varName)) {
        return;
    }
    visited.add(varName);

    if (!objectDependencies.has(varName)) {
        return;
    }

    for (const dependency of objectDependencies.get(varName)) {
        if (!output.has(dependency)) {
            output.add(dependency);
        }
        expandDependencies(dependency, objectDependencies, output, visited);
    }
}

function resolveEscapedVariables(expression, localVars, localObjectVars, objectDependencies) {
    const escapedVars = new Set();
    const ids = extractIdentifiers(expression);

    for (const id of ids) {
        if (localVars.has(id) || localObjectVars.has(id)) {
            escapedVars.add(id);
            expandDependencies(id, objectDependencies, escapedVars);
        }
    }

    return escapedVars;
}

function addEscape(escapes, dedupe, escape) {
    const key = `${escape.escape_type}|${escape.line}|${escape.variable_name}|${escape.reason}`;
    if (!dedupe.has(key)) {
        dedupe.add(key);
        escapes.push(escape);
    }
}

/**
 * Analyze a JavaScript file for escape patterns
 */
function analyzeFile(sourceFile, functionName) {
    try {
        const source = fs.readFileSync(sourceFile, 'utf8');
        const lines = source.split('\n');
        const escapes = [];
        const dedupe = new Set();
        const moduleRetainers = collectModuleRetainers(lines);
        
        // Find the function
        let inTargetFunction = false;
        let braceDepth = 0;
        let functionStartLine = -1;
        const timerHandles = new Set();
        const clearedHandles = new Set();
        const unawaitedPromises = new Set();
        const awaitedPromises = new Set();
        const setTimeoutCalls = [];  // Track all setTimeout calls
        const clearTimeoutCalls = [];  // Track all clearTimeout calls
        const localVars = new Set();
        const localObjectVars = new Set();
        const objectDependencies = new Map();
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            const lineNum = i + 1;
            
            if (!inTargetFunction) {
                // Look for function definition
                const funcMatch = trimmed.match(/(?:function\s+|const\s+|let\s+|var\s+|async\s+)(\w+)\s*[=\(]/);
                if (funcMatch && funcMatch[1] === functionName) {
                    inTargetFunction = true;
                    functionStartLine = lineNum;
                    braceDepth = 0;
                    if (trimmed.includes('{')) {
                        braceDepth++;
                    }
                }
            } else {
                // Count braces
                braceDepth += (trimmed.match(/{/g) || []).length;
                braceDepth -= (trimmed.match(/}/g) || []).length;

                const assignmentMatch = trimmed.match(/(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(.+?);?$/);
                if (assignmentMatch) {
                    const localName = assignmentMatch[1];
                    const rhs = assignmentMatch[2];
                    localVars.add(localName);

                    if (looksLikeObjectInitializer(rhs)) {
                        localObjectVars.add(localName);
                    }

                    const referencedLocals = extractIdentifiers(rhs)
                        .filter((id) => id !== localName && (localVars.has(id) || localObjectVars.has(id)));
                    if (referencedLocals.length > 0) {
                        objectDependencies.set(localName, new Set(referencedLocals));
                    }
                }

                const retainedStoreCall = trimmed.match(/([A-Za-z_$][\w$]*)\.(set|push|unshift|add)\((.*)\)\s*;?$/);
                if (retainedStoreCall) {
                    const containerName = retainedStoreCall[1];
                    const method = retainedStoreCall[2];
                    const args = retainedStoreCall[3] || '';

                    if (isRetainerContainer(containerName, moduleRetainers)) {
                        const escapedVars = resolveEscapedVariables(args, localVars, localObjectVars, objectDependencies);
                        const isClosureRetention = args.includes('=>') || args.includes('function');

                        for (const escapedVar of escapedVars) {
                            const escapeType = isClosureRetention ? 'closure' : 'global';
                            const reason = isClosureRetention
                                ? `Local object '${escapedVar}' captured by retained closure in '${containerName}.${method}'`
                                : `Local object '${escapedVar}' stored in retained container '${containerName}'`;

                            addEscape(escapes, dedupe, {
                                escape_type: escapeType,
                                line: lineNum,
                                column: Math.max(trimmed.indexOf(containerName), 0),
                                variable_name: escapedVar,
                                reason,
                                confidence: 'high',
                                code_snippet: trimmed
                            });
                        }
                    }
                }

                const retainedIndexAssignment = trimmed.match(/([A-Za-z_$][\w$]*)\s*\[[^\]]+\]\s*=\s*(.+);?$/);
                if (retainedIndexAssignment) {
                    const containerName = retainedIndexAssignment[1];
                    const rhs = retainedIndexAssignment[2] || '';
                    if (isRetainerContainer(containerName, moduleRetainers)) {
                        const escapedVars = resolveEscapedVariables(rhs, localVars, localObjectVars, objectDependencies);
                        for (const escapedVar of escapedVars) {
                            addEscape(escapes, dedupe, {
                                escape_type: 'global',
                                line: lineNum,
                                column: Math.max(trimmed.indexOf(containerName), 0),
                                variable_name: escapedVar,
                                reason: `Local object '${escapedVar}' assigned into retained container '${containerName}'`,
                                confidence: 'high',
                                code_snippet: trimmed
                            });
                        }
                    }
                }

                const retainedDirectAssignment = trimmed.match(/^([A-Za-z_$][\w$]*)\s*=\s*(.+);?$/);
                if (retainedDirectAssignment) {
                    const lhs = retainedDirectAssignment[1];
                    const rhs = retainedDirectAssignment[2] || '';
                    if (isRetainerContainer(lhs, moduleRetainers)) {
                        const escapedVars = resolveEscapedVariables(rhs, localVars, localObjectVars, objectDependencies);
                        for (const escapedVar of escapedVars) {
                            addEscape(escapes, dedupe, {
                                escape_type: 'global',
                                line: lineNum,
                                column: Math.max(trimmed.indexOf(lhs), 0),
                                variable_name: escapedVar,
                                reason: `Local object '${escapedVar}' assigned to retained binding '${lhs}'`,
                                confidence: 'high',
                                code_snippet: trimmed
                            });
                        }
                    }
                }

                const returnObjectMatch = trimmed.match(/^return\s+([A-Za-z_$][\w$]*)\s*;?$/);
                if (returnObjectMatch) {
                    const returnedName = returnObjectMatch[1];
                    if (localObjectVars.has(returnedName) || objectDependencies.has(returnedName)) {
                        addEscape(escapes, dedupe, {
                            escape_type: 'return',
                            line: lineNum,
                            column: Math.max(trimmed.indexOf(returnedName), 0),
                            variable_name: returnedName,
                            reason: `Local object '${returnedName}' returned from function`,
                            confidence: 'high',
                            code_snippet: trimmed
                        });
                    }
                }
                
                // Check for setTimeout without clearTimeout
                if (trimmed.includes('setTimeout') && !trimmed.includes('await')) {
                    const varMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=/);
                    if (varMatch) {
                        timerHandles.add(varMatch[1]);
                        setTimeoutCalls.push({var: varMatch[1], line: lineNum});
                    } else {
                        // setTimeout called without storing the handle - likely a leak
                        addEscape(escapes, dedupe, {
                            escape_type: 'concurrency',
                            line: lineNum,
                            column: trimmed.indexOf('setTimeout'),
                            variable_name: 'setTimeout',
                            reason: 'setTimeout called without storing handle for cleanup',
                            confidence: 'medium',
                            code_snippet: trimmed
                        });
                    }
                }
                
                // Check for setInterval (always a problem if not cleared)
                if (trimmed.includes('setInterval')) {
                    const varMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=/);
                    if (varMatch) {
                        timerHandles.add(varMatch[1]);
                        setTimeoutCalls.push({var: varMatch[1], line: lineNum});
                    } else {
                        addEscape(escapes, dedupe, {
                            escape_type: 'concurrency',
                            line: lineNum,
                            column: trimmed.indexOf('setInterval'),
                            variable_name: 'setInterval',
                            reason: 'setInterval called without storing handle for cleanup',
                            confidence: 'high',
                            code_snippet: trimmed
                        });
                    }
                }
                
                // Check for clearTimeout/clearInterval calls
                const clearMatch = trimmed.match(/clear(?:Timeout|Interval)\((\w+)\)/);
                if (clearMatch) {
                    clearedHandles.add(clearMatch[1]);
                    clearTimeoutCalls.push({var: clearMatch[1], line: lineNum});
                }
                
                // Check for process.nextTick without completion
                if (trimmed.includes('process.nextTick')) {
                    addEscape(escapes, dedupe, {
                        escape_type: 'concurrency',
                        line: lineNum,
                        column: trimmed.indexOf('process.nextTick'),
                        variable_name: 'nextTick',
                        reason: 'process.nextTick may defer execution beyond function return',
                        confidence: 'low',
                        code_snippet: trimmed
                    });
                }
                
                // Check for setImmediate
                if (trimmed.includes('setImmediate')) {
                    const varMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=/);
                    if (!varMatch) {
                        addEscape(escapes, dedupe, {
                            escape_type: 'concurrency',
                            line: lineNum,
                            column: trimmed.indexOf('setImmediate'),
                            variable_name: 'setImmediate',
                            reason: 'setImmediate called without storing handle',
                            confidence: 'medium',
                            code_snippet: trimmed
                        });
                    }
                }
                
                // Check for Promises/async - detect .then() without .catch() or await
                const promiseMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=\s*(?:new\s+)?Promise|\.then\(|\.catch\(|\.finally\(/);
                if (promiseMatch && trimmed.includes('Promise')) {
                    const varMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=/);
                    if (varMatch) {
                        unawaitedPromises.add(varMatch[1]);
                    }
                }
                
                // Check for await/catch to mark promises as handled
                if (trimmed.includes('await ') || trimmed.includes('.catch(')) {
                    const names = trimmed.match(/\b(\w+)\b/g) || [];
                    names.forEach(name => awaitedPromises.add(name));
                }
                
                // Check for async callbacks without await
                if (trimmed.includes('.then(') && !trimmed.includes('await')) {
                    const varMatch = trimmed.match(/(\w+)\.then\(/);
                    if (varMatch) {
                        unawaitedPromises.add(varMatch[1]);
                    }
                }
                
                if (braceDepth === 0) {
                    // End of function - check for uncleared timers
                    for (const handle of timerHandles) {
                        if (!clearedHandles.has(handle)) {
                            addEscape(escapes, dedupe, {
                                escape_type: 'concurrency',
                                line: lineNum,
                                column: 0,
                                variable_name: handle,
                                reason: `Timer handle '${handle}' created but not cleared`,
                                confidence: 'high',
                                code_snippet: null
                            });
                        }
                    }
                    
                    // Check for unawaited promises
                    for (const promise of unawaitedPromises) {
                        if (!awaitedPromises.has(promise)) {
                            addEscape(escapes, dedupe, {
                                escape_type: 'concurrency',
                                line: lineNum,
                                column: 0,
                                variable_name: promise,
                                reason: `Promise '${promise}' created but not awaited or handled`,
                                confidence: 'medium',
                                code_snippet: null
                            });
                        }
                    }
                    break;
                }
            }
        }
        
        return {
            escapes: escapes,
            success: true
        };
        
    } catch (error) {
        return {
            escapes: [],
            success: false,
            error: error.message
        };
    }
}

// Main entry point
if (require.main === module) {
    if (process.argv.length !== 4) {
        console.log(JSON.stringify({
            escapes: [],
            success: false,
            error: 'Usage: static_analyzer.js <source_file> <function_name>'
        }, null, 2));
        process.exit(1);
    }
    
    const sourceFile = process.argv[2];
    const functionName = process.argv[3];
    
    const result = analyzeFile(sourceFile, functionName);
    console.log(JSON.stringify(result, null, 2));
}

module.exports = { analyzeFile };
