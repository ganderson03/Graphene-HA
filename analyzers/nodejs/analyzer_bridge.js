#!/usr/bin/env node
const path = require('path');
const async_hooks = require('async_hooks');
const { analyzeFile: runStaticAnalyzer } = require('./static_analyzer');

const TRADITIONAL_ESCAPE_TYPES = new Set(['return', 'parameter', 'global', 'closure', 'heap']);
const ESCAPE_DESTINATIONS = {
    return: 'caller',
    parameter: 'callee',
    global: 'module_scope',
    closure: 'closure_scope',
    heap: 'heap_container'
};
const IGNORED_ASYNC_RESOURCE_TYPES = new Set([
    'Timeout',
    'TIMERWRAP',
    'Immediate',
    'TickObject',
    'PROMISE',
    'Microtask'
]);

class AsyncResourceTracker {
    constructor() {
        this.baselineResources = new Set();
        this.currentResources = new Map();
        this.hook = null;
    }

    start() {
        this.baselineResources.clear();
        this.currentResources.clear();
        this.hook = async_hooks.createHook({
            init: (asyncId, type) => this.currentResources.set(asyncId, {type, created: Date.now()}),
            destroy: (asyncId) => this.currentResources.delete(asyncId)
        });
        this.hook.enable();
    }

    captureBaseline() {
        this.baselineResources = new Set(this.currentResources.keys());
    }

    stop() {
        if (this.hook) this.hook.disable();
    }

    getEscapedResources() {
        const escaped = [];
        for (const [asyncId, info] of this.currentResources.entries()) {
            if (!this.baselineResources.has(asyncId) && !IGNORED_ASYNC_RESOURCE_TYPES.has(info.type)) {
                escaped.push({task_id: String(asyncId), task_type: info.type, state: 'active'});
            }
        }
        return escaped;
    }
}

function parseTargetReference(target) {
    const delimiterIndex = target.lastIndexOf(':');
    if (delimiterIndex <= 0 || delimiterIndex >= target.length - 1) {
        throw new Error(`Invalid target format '${target}': must be 'file.js:functionName' or 'module:functionName'`);
    }

    const modulePath = target.slice(0, delimiterIndex).trim();
    const functionName = target.slice(delimiterIndex + 1).trim();
    if (!modulePath || !functionName) {
        throw new Error(`Invalid target format '${target}': module path and function name are required`);
    }

    const normalizedModulePath = modulePath.replace(/\\/g, path.sep);
    const isPathTarget = /[\\/]/.test(modulePath) || /\.(js|mjs|cjs)$/i.test(modulePath);

    return {
        modulePath,
        functionName,
        normalizedModulePath,
        isPathTarget
    };
}

function resolveModuleCandidates(normalizedModulePath) {
    const workspaceRoot = path.resolve(__dirname, '..', '..');
    const candidates = [];

    if (path.isAbsolute(normalizedModulePath)) {
        candidates.push(path.normalize(normalizedModulePath));
    }
    candidates.push(path.resolve(process.cwd(), normalizedModulePath));
    candidates.push(path.resolve(workspaceRoot, normalizedModulePath));

    return [...new Set(candidates)];
}

function summarizeStaticEscapes(escapes) {
    if (!escapes.length) {
        return '';
    }

    const fragments = escapes.map((escape) => {
        const lineSuffix = Number.isInteger(escape.line) && escape.line > 0 ? `@L${escape.line}` : '';
        return `${escape.escape_type}:${escape.variable_name || '<value>'}${lineSuffix}`;
    });

    return fragments.join('; ');
}

function convertStaticEscapesToProtocol(escapes, sourcePath) {
    const details = emptyEscapeDetails();

    for (const escape of escapes) {
        const line = Number.isInteger(escape.line) ? escape.line : 0;
        const column = Number.isInteger(escape.column) ? escape.column : 0;
        const variableName = escape.variable_name || '<value>';
        const escapeType = escape.escape_type || 'unknown';
        const confidence = escape.confidence || 'medium';
        const allocationSite = sourcePath
            ? `${sourcePath}:${line}:${column}`
            : 'unknown';

        details.escaping_references.push({
            variable_name: variableName,
            object_type: 'unknown',
            allocation_site: allocationSite,
            escaped_via: escapeType
        });

        details.escape_paths.push({
            source: variableName,
            destination: ESCAPE_DESTINATIONS[escapeType] || 'unknown',
            escape_type: escapeType,
            confidence
        });
    }

    return details;
}

function runTraditionalStaticEscapeAnalysis(sourcePath, functionName) {
    if (!sourcePath || !functionName) {
        return {
            detected: false,
            escapes: [],
            details: emptyEscapeDetails(),
            summary: ''
        };
    }

    try {
        const analysis = runStaticAnalyzer(sourcePath, functionName);
        if (!analysis || !analysis.success || !Array.isArray(analysis.escapes)) {
            return {
                detected: false,
                escapes: [],
                details: emptyEscapeDetails(),
                summary: ''
            };
        }

        const escapes = analysis.escapes.filter((escape) => TRADITIONAL_ESCAPE_TYPES.has(escape.escape_type));
        if (escapes.length === 0) {
            return {
                detected: false,
                escapes: [],
                details: emptyEscapeDetails(),
                summary: ''
            };
        }

        return {
            detected: true,
            escapes,
            details: convertStaticEscapesToProtocol(escapes, sourcePath),
            summary: summarizeStaticEscapes(escapes)
        };
    } catch (_) {
        return {
            detected: false,
            escapes: [],
            details: emptyEscapeDetails(),
            summary: ''
        };
    }
}

function loadTargetFunction(target) {
    const parsedTarget = parseTargetReference(target);
    const modulePath = parsedTarget.modulePath;
    const functionName = parsedTarget.functionName;
    let loadedModule;
    let resolvedSourcePath = null;

    try {
        if (parsedTarget.isPathTarget) {
            const candidates = resolveModuleCandidates(parsedTarget.normalizedModulePath);
            let moduleLoadError = null;
            for (const candidate of candidates) {
                try {
                    loadedModule = require(candidate);
                    resolvedSourcePath = candidate;
                    moduleLoadError = null;
                    break;
                } catch (error) {
                    moduleLoadError = error;
                }
            }

            if (!loadedModule) {
                if (moduleLoadError) {
                    throw moduleLoadError;
                }
                throw new Error(`Module file '${modulePath}' could not be resolved`);
            }
        } else {
            loadedModule = require(modulePath);
            try {
                resolvedSourcePath = require.resolve(modulePath);
            } catch (_) {
                resolvedSourcePath = null;
            }
        }

        if (typeof loadedModule[functionName] !== 'function') {
            const availableFunctions = Object.keys(loadedModule).filter((key) => typeof loadedModule[key] === 'function');
            const preview = availableFunctions.slice(0, 5);
            throw new ReferenceError(`Function '${functionName}' not found in module (available: ${preview.join(', ')}${availableFunctions.length > 5 ? '...' : ''})`);
        }

        return {
            targetFunc: loadedModule[functionName],
            functionName,
            sourcePath: resolvedSourcePath
        };
    } catch (error) {
        if (error instanceof ReferenceError) throw error;
        throw new Error(`Failed to load module '${modulePath}': ${error.message}`);
    }
}

function diagnoseBridgeError(errorMsg) {
    const raw = String(errorMsg || '').trim();
    const lower = raw.toLowerCase();

    if (lower.includes('timeout') || lower.includes('timed out') || lower.includes('exceeded')) {
        return {
            category: 'Timeout',
            suggestedAction: 'Inspect blocking operations and missing joins/awaits before increasing timeout.'
        };
    }

    if (
        lower.includes('target resolution')
        || lower.includes("missing required field: 'target'")
        || lower.includes('failed to load')
        || lower.includes('invalid target')
        || lower.includes('module not found')
        || lower.includes('function') && lower.includes('not found')
    ) {
        return {
            category: 'Target Resolution',
            suggestedAction: 'Verify target signature/path and ensure the target symbol exists in the selected language module.'
        };
    }

    if (
        lower.includes('protocol/input')
        || lower.includes('invalid json')
        || lower.includes('failed to parse')
        || lower.includes('empty input')
        || lower.includes('expected json')
        || lower.includes('json')
        || lower.includes('parse')
        || lower.includes('stdin')
        || lower.includes('protocol')
    ) {
        return {
            category: 'Protocol/Input',
            suggestedAction: 'Validate request JSON and ensure bridge stdin/stdout protocol fields match the orchestrator contract.'
        };
    }

    if (
        lower.includes('environment')
        || lower.includes('permission denied')
        || lower.includes('not available')
        || lower.includes('not found in path')
        || lower.includes('command not found')
        || lower.includes('missing tools')
        || lower.includes('node.js not found')
    ) {
        return {
            category: 'Environment',
            suggestedAction: 'Check runtime/toolchain installation and PATH configuration for the selected language analyzer.'
        };
    }

    if (
        lower.includes('runtime crash')
        || lower.includes('panic')
        || lower.includes('exception')
        || lower.includes('traceback')
        || lower.includes('segmentation')
    ) {
        return {
            category: 'Runtime Crash',
            suggestedAction: 'Re-run with --verbose and inspect bridge stack traces for runtime exceptions.'
        };
    }

    return {
        category: 'Unknown',
        suggestedAction: 'Re-run with --verbose and inspect bridge stdout/stderr for additional diagnostics.'
    };
}

function emptyEscapeDetails() {
    return {
        escaping_references: [],
        escape_paths: [],
        threads: [],
        processes: [],
        async_tasks: [],
        goroutines: [],
        other: []
    };
}

function mergeEscapeDetails(primary, secondary) {
    const merged = emptyEscapeDetails();
    const first = primary || {};
    const second = secondary || {};

    const mergeArrayField = (key) => {
        merged[key] = [
            ...(Array.isArray(first[key]) ? first[key] : []),
            ...(Array.isArray(second[key]) ? second[key] : [])
        ];
    };

    mergeArrayField('escaping_references');
    mergeArrayField('escape_paths');
    mergeArrayField('threads');
    mergeArrayField('processes');
    mergeArrayField('async_tasks');
    mergeArrayField('goroutines');
    mergeArrayField('other');

    return merged;
}

async function executeTest(targetFunc, targetLabel, input, timeoutSeconds) {
    const result = {input_data: input, success: false, crashed: false, output: '', error: '', execution_time_ms: 0, escape_detected: false, escape_details: emptyEscapeDetails()};
    const tracker = new AsyncResourceTracker();
    tracker.start();
    await new Promise((resolve) => setImmediate(resolve));
    tracker.captureBaseline();

    const heapBefore = captureHeapSnapshot();

    const startTime = Date.now();
    let timeoutHandle = null;

    try {
        const returnValue = await Promise.race([
            Promise.resolve().then(() => targetFunc(input)),
            new Promise((_, reject) => {
                timeoutHandle = setTimeout(() => reject(new Error(`Function timeout after ${timeoutSeconds}s`)), timeoutSeconds * 1000);
            })
        ]);
        result.output = String(returnValue);
        result.success = true;
    } catch (error) {
        result.crashed = true;
        result.error = `${error.name}: ${error.message}`;
    } finally {
        if (timeoutHandle !== null) {
            clearTimeout(timeoutHandle);
        }
    }

    result.execution_time_ms = Date.now() - startTime;
    await new Promise(resolve => setTimeout(resolve, 100));

    const heapAfter = captureHeapSnapshot();
    const heapGrowthBytes = Math.max(0, heapAfter.heap_used_bytes - heapBefore.heap_used_bytes);
    const heapPeakBytes = Math.max(heapAfter.heap_total_bytes, heapBefore.heap_total_bytes);

    if (heapGrowthBytes > 0) {
        const label = String(targetLabel || '<anonymous>');
        result.escape_details.escaping_references.push({
            variable_name: label,
            object_type: 'heap_allocation_delta',
            allocation_site: label,
            escaped_via: 'heap'
        });

        result.escape_details.escape_paths.push({
            source: label,
            destination: 'heap_container',
            escape_type: 'heap',
            confidence: heapGrowthBytes >= 1024 ? 'high' : 'medium'
        });

        result.escape_details.other.push(`heap_growth_bytes:${heapGrowthBytes}`);
        result.escape_details.other.push(`heap_used_before_bytes:${heapBefore.heap_used_bytes}`);
        result.escape_details.other.push(`heap_used_after_bytes:${heapAfter.heap_used_bytes}`);
        result.escape_details.other.push(`heap_peak_bytes:${heapPeakBytes}`);
    }

    const escapedResources = tracker.getEscapedResources();
    result.escape_details.async_tasks = escapedResources;
    result.escape_detected = escapedResources.length > 0 || result.escape_details.escaping_references.length > 0;
    tracker.stop();
    return result;
}

function captureHeapSnapshot() {
    if (typeof global.gc === 'function') {
        try {
            global.gc();
        } catch (_) {
            // Best-effort GC; continue with current memory view.
        }
    }

    const usage = process.memoryUsage();
    return {
        heap_used_bytes: Math.max(0, usage.heapUsed || 0),
        heap_total_bytes: Math.max(0, usage.heapTotal || 0)
    };
}

function findHeapSignal(entries, prefix) {
    if (!Array.isArray(entries)) {
        return null;
    }
    return entries.find((entry) => typeof entry === 'string' && entry.startsWith(prefix)) || null;
}

function errorResponse(error, sessionId = 'unknown') {
    const errorMsg = error instanceof Error 
        ? `${error.name}: ${error.message}`
        : typeof error === 'string' ? error : 'Unknown error';
    const diagnosis = diagnoseBridgeError(errorMsg);
    return {
        session_id: sessionId,
        language: 'javascript',
        analyzer_version: '1.0.0',
        analysis_mode: 'dynamic',
        results: [{
            input_data: '<bridge-startup>',
            success: false,
            crashed: true,
            output: '',
            error: `${diagnosis.category}: ${errorMsg}`,
            execution_time_ms: 0,
            escape_detected: false,
            escape_details: emptyEscapeDetails()
        }],
        vulnerabilities: [],
        summary: {total_tests: 1, successes: 0, crashes: 1, timeouts: diagnosis.category === 'Timeout' ? 1 : 0, escapes: 0, genuine_escapes: 0, crash_rate: 1.0},
        error: `Bridge error: ${errorMsg}`,
        error_category: diagnosis.category,
        suggested_action: diagnosis.suggestedAction
    };
}

async function analyze(request) {
    const sessionId = request.session_id || request.sessionId || 'unknown';
    const analysisMode = request.analysis_mode || request.analysisMode || 'dynamic';
    const response = {session_id: sessionId, language: 'javascript', analyzer_version: '1.0.0', analysis_mode: analysisMode, results: [], vulnerabilities: [], summary: {total_tests: 0, successes: 0, crashes: 0, timeouts: 0, escapes: 0, genuine_escapes: 0, crash_rate: 0}};
    try {
        if (!request.target) throw new Error("Missing required field: 'target'");
        if (!Array.isArray(request.inputs)) throw new Error("Missing or invalid field: 'inputs' must be an array");
        
        const loadedTarget = loadTargetFunction(request.target);
        let successes = 0, crashes = 0, timeouts = 0, escapes = 0, genuineEscapes = 0;
        
        for (const input of request.inputs) {
            for (let i = 0; i < (request.repeat || 1); i++) {
                const timeoutSeconds = request.timeout_seconds || request.timeoutSeconds || 30;
                const result = await executeTest(loadedTarget.targetFunc, request.target, input, timeoutSeconds);

                response.results.push(result);
                if (result.success) successes++;
                if (result.crashed) crashes++;
                if (result.error.includes('timeout')) timeouts++;
                if (result.escape_detected) {
                    escapes++;
                    if (!result.error.includes('timeout')) genuineEscapes++;

                    const asyncCount = result.escape_details.async_tasks.length;
                    const heapSignal = findHeapSignal(result.escape_details.other, 'heap_growth_bytes:');
                    const description = heapSignal
                        ? `Node.js heap escape signal detected (${heapSignal})${asyncCount > 0 ? ` + ${asyncCount} async resource leak(s)` : ''}`
                        : `${asyncCount} async resource(s) escaped`;

                    response.vulnerabilities.push({
                        input,
                        vulnerability_type: 'object_escape',
                        severity: 'high',
                        description,
                        escape_details: result.escape_details
                    });
                }
            }
        }
        const totalTests = response.results.length;
        response.summary = {total_tests: totalTests, successes, crashes, timeouts, escapes, genuine_escapes: genuineEscapes, crash_rate: totalTests > 0 ? crashes / totalTests : 0};
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        const diagnosis = diagnoseBridgeError(errorMsg);
        response.results = [{
            input_data: '<bridge-startup>',
            success: false,
            crashed: true,
            output: '',
            error: `${diagnosis.category}: ${errorMsg}`,
            execution_time_ms: 0,
            escape_detected: false,
            escape_details: emptyEscapeDetails()
        }];
        response.summary.total_tests = 1;
        response.summary.crash_rate = 1.0;
        response.summary.crashes = 1;
        response.summary.successes = 0;
        response.summary.timeouts = diagnosis.category === 'Timeout' ? 1 : 0;
        response.error = errorMsg;
        response.error_category = diagnosis.category;
        response.suggested_action = diagnosis.suggestedAction;
    }
    return response;
}

async function main() {
    try {
        const chunks = [];
        for await (const chunk of process.stdin) {
            chunks.push(chunk);
        }
        const inputData = Buffer.concat(chunks).toString('utf8');
        
        if (!inputData.trim()) {
            console.error(JSON.stringify(errorResponse(new Error('Empty input: expected JSON request on stdin'))));
            process.exit(1);
        }
        
        let request;
        try {
            request = JSON.parse(inputData);
        } catch (parseError) {
            const e = parseError instanceof SyntaxError ? parseError : new Error(String(parseError));
            console.error(JSON.stringify(errorResponse(new Error(`Invalid JSON: ${e.message}`))));
            process.exit(1);
        }
        
        const response = await analyze(request);
        console.log(JSON.stringify(response, null, 2));
        process.exit(response.error ? 1 : 0);
    } catch (error) {
        console.error(JSON.stringify(errorResponse(error)));
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { analyze, executeTest, loadTargetFunction };
