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
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            const lineNum = i + 1;
            
            if (!inTargetFunction) {
                // Look for function definition
                const funcMatch = trimmed.match(/(?:function\s+|const\s+|let\s+|var\s+)(\w+)\s*[=\(]/);
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
                
                // Check for setInterval without clearInterval
                if (trimmed.includes('setInterval')) {
                    const varMatch = trimmed.match(/(?:const|let|var)\s+(\w+)\s*=/);
                    if (varMatch) {
                        timerHandles.add(varMatch[1]);
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
                
                if (braceDepth === 0) {
                    // End of function - check for uncleared timers
                    for (const handle of timerHandles) {
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
