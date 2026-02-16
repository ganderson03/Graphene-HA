#!/usr/bin/env node
/**
 * Node.js Analyzer Bridge - Detects escaping async resources
 * Uses async_hooks to track async operations that outlive function execution
 */

const fs = require('fs');
const path = require('path');
const { AsyncLocalStorage } = require('async_hooks');
const async_hooks = require('async_hooks');
const { Worker } = require('worker_threads');
const { spawn } = require('child_process');

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
            init: (asyncId, type, triggerAsyncId) => {
                this.currentResources.set(asyncId, {
                    type,
                    triggerAsyncId,
                    created: Date.now()
                });
            },
            destroy: (asyncId) => {
                this.currentResources.delete(asyncId);
            }
        });

        this.hook.enable();

        // Capture baseline
        setTimeout(() => {
            this.baselineResources = new Set(this.currentResources.keys());
        }, 10);
    }

    stop() {
        if (this.hook) {
            this.hook.disable();
        }
    }

    getEscapedResources() {
        const escaped = [];
        for (const [asyncId, info] of this.currentResources.entries()) {
            if (!this.baselineResources.has(asyncId)) {
                // Filter out common system resources
                if (!['TIMERWRAP', 'Immediate', 'TickObject'].includes(info.type)) {
                    escaped.push({
                        taskId: String(asyncId),
                        taskType: info.type,
                        state: 'active'
                    });
                }
            }
        }
        return escaped;
    }
}

function loadTargetFunction(target) {
    // Parse target: file.js:functionName or module:functionName
    const parts = target.split(':');
    if (parts.length < 2) {
        throw new Error('Target must be file.js:functionName or module:functionName');
    }

    const modulePath = parts[0];
    const functionName = parts[1];

    let module;
    if (modulePath.endsWith('.js') || modulePath.endsWith('.mjs')) {
        const absolutePath = path.resolve(modulePath);
        module = require(absolutePath);
    } else {
        module = require(modulePath);
    }

    if (typeof module[functionName] !== 'function') {
        throw new Error(`Function '${functionName}' not found in module`);
    }

    return module[functionName];
}

async function executeTest(targetFunc, input, timeoutSeconds) {
    const result = {
        inputData: input,
        success: false,
        crashed: false,
        output: '',
        error: '',
        executionTimeMs: 0,
        escapeDetected: false,
        escapeDetails: {
            threads: [],
            processes: [],
            asyncTasks: [],
            goroutines: [],
            other: []
        }
    };

    const tracker = new AsyncResourceTracker();
    tracker.start();

    const startTime = Date.now();

    try {
        // Execute the function with timeout
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Timeout exceeded')), timeoutSeconds * 1000)
        );

        const execPromise = Promise.resolve(targetFunc(input));

        const returnValue = await Promise.race([execPromise, timeoutPromise]);

        result.output = String(returnValue);
        result.success = true;

    } catch (error) {
        result.crashed = true;
        result.error = `${error.name}: ${error.message}`;
    }

    result.executionTimeMs = Date.now() - startTime;

    // Wait a bit for async operations to settle
    await new Promise(resolve => setTimeout(resolve, 100));

    // Check for escaped resources
    const escapedResources = tracker.getEscapedResources();
    result.escapeDetails.asyncTasks = escapedResources;
    result.escapeDetected = escapedResources.length > 0;

    tracker.stop();

    return result;
}

async function analyze(request) {
    const response = {
        sessionId: request.sessionId,
        language: 'javascript',
        analyzerVersion: '1.0.0',
        results: [],
        vulnerabilities: [],
        summary: {
            totalTests: 0,
            successes: 0,
            crashes: 0,
            timeouts: 0,
            escapes: 0,
            genuineEscapes: 0,
            crashRate: 0
        }
    };

    try {
        // Load target function
        const targetFunc = loadTargetFunction(request.target);

        // Run tests
        let successes = 0, crashes = 0, timeouts = 0, escapes = 0, genuineEscapes = 0;

        for (const input of request.inputs) {
            for (let i = 0; i < request.repeat; i++) {
                const result = await executeTest(targetFunc, input, request.timeoutSeconds);
                response.results.push(result);

                if (result.success) successes++;
                if (result.crashed) crashes++;
                if (result.error.includes('Timeout')) timeouts++;
                if (result.escapeDetected) {
                    escapes++;
                    if (!result.error.includes('Timeout')) {
                        genuineEscapes++;
                    }

                    // Add vulnerability
                    response.vulnerabilities.push({
                        input: input,
                        vulnerabilityType: 'concurrent_escape',
                        severity: 'high',
                        description: `${result.escapeDetails.asyncTasks.length} async resource(s) escaped`,
                        escapeDetails: result.escapeDetails
                    });
                }
            }
        }

        // Summary
        const totalTests = response.results.length;
        response.summary = {
            totalTests,
            successes,
            crashes,
            timeouts,
            escapes,
            genuineEscapes,
            crashRate: totalTests > 0 ? crashes / totalTests : 0
        };

    } catch (error) {
        response.summary.crashes = 1;
        response.summary.crashRate = 1.0;
        response.error = error.message;
    }

    return response;
}

async function main() {
    try {
        // Read request from stdin
        const chunks = [];
        for await (const chunk of process.stdin) {
            chunks.push(chunk);
        }
        const requestJson = Buffer.concat(chunks).toString('utf8');
        const request = JSON.parse(requestJson);

        // Process request
        const response = await analyze(request);

        // Write response to stdout
        console.log(JSON.stringify(response, null, 2));
        process.exit(0);

    } catch (error) {
        const errorResponse = {
            sessionId: 'unknown',
            language: 'javascript',
            analyzerVersion: '1.0.0',
            results: [],
            vulnerabilities: [],
            summary: {
                totalTests: 0,
                successes: 0,
                crashes: 1,
                timeouts: 0,
                escapes: 0,
                genuineEscapes: 0,
                crashRate: 1.0
            },
            error: `Bridge error: ${error.message}`
        };

        console.error(JSON.stringify(errorResponse));
        console.error(error.stack);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { analyze, executeTest, loadTargetFunction };
