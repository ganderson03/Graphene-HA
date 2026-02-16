#!/usr/bin/env node
/**
 * JavaScript/Node.js Static Escape Analyzer
 * Detects concurrency escapes in JavaScript/Node.js code
 */

const fs = require('fs');

/**
 * Analyze a JavaScript file for escape patterns
 */
function analyzeFile(sourceFile, functionName) {
    try {
        const source = fs.readFileSync(sourceFile, 'utf8');
        const lines = source.split('\n');
        const escapes = [];
        
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
                
                // Check for setTimeout without clearTimeout
                if (trimmed.includes('setTimeout') && !trimmed.includes('await')) {
                    const varMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=/);
                    if (varMatch) {
                        timerHandles.add(varMatch[1]);
                        setTimeoutCalls.push({var: varMatch[1], line: lineNum});
                    } else {
                        // setTimeout called without storing the handle - likely a leak
                        escapes.push({
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
                        escapes.push({
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
                    escapes.push({
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
                        escapes.push({
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
                    // End of function - check for uncleared timers\n                    for (const handle of timerHandles) {
                        if (!clearedHandles.has(handle)) {
                            escapes.push({
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
                            escapes.push({
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
