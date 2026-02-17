#!/usr/bin/env node
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
            init: (asyncId, type) => this.currentResources.set(asyncId, {type, created: Date.now()}),
            destroy: (asyncId) => this.currentResources.delete(asyncId)
        });
        this.hook.enable();
        setTimeout(() => {
            this.baselineResources = new Set(this.currentResources.keys());
        }, 10);
    }
    stop() {
        if (this.hook) this.hook.disable();
    }
    getEscapedResources() {
        const escaped = [];
        for (const [asyncId, info] of this.currentResources.entries()) {
            if (!this.baselineResources.has(asyncId) && !['TIMERWRAP', 'Immediate', 'TickObject'].includes(info.type)) {
                escaped.push({taskId: String(asyncId), taskType: info.type, state: 'active'});
            }
        }
        return escaped;
    }
}

function loadTargetFunction(target) {
    const parts = target.split(':');
    if (parts.length < 2) throw new Error('Target must be file.js:functionName or module:functionName');
    const modulePath = parts[0];
    const functionName = parts[1];
    const module = modulePath.endsWith('.js') || modulePath.endsWith('.mjs') ? require(path.resolve(modulePath)) : require(modulePath);
    if (typeof module[functionName] !== 'function') throw new Error(`Function '${functionName}' not found in module`);
    return module[functionName];
}

async function executeTest(targetFunc, input, timeoutSeconds) {
    const result = {inputData: input, success: false, crashed: false, output: '', error: '', executionTimeMs: 0, escapeDetected: false, escapeDetails: {threads: [], processes: [], asyncTasks: [], goroutines: [], other: []}};
    const tracker = new AsyncResourceTracker();
    tracker.start();
    const startTime = Date.now();
    try {
        const returnValue = await Promise.race([Promise.resolve(targetFunc(input)), new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout exceeded')), timeoutSeconds * 1000))]);
        result.output = String(returnValue);
        result.success = true;
    } catch (error) {
        result.crashed = true;
        result.error = `${error.name}: ${error.message}`;
    }
    result.executionTimeMs = Date.now() - startTime;
    await new Promise(resolve => setTimeout(resolve, 100));
    const escapedResources = tracker.getEscapedResources();
    result.escapeDetails.asyncTasks = escapedResources;
    result.escapeDetected = escapedResources.length > 0;
    tracker.stop();
    return result;
}

function errorResponse(error, sessionId = 'unknown') {
    return {sessionId, language: 'javascript', analyzerVersion: '1.0.0', results: [], vulnerabilities: [], summary: {totalTests: 0, successes: 0, crashes: 1, timeouts: 0, escapes: 0, genuineEscapes: 0, crashRate: 1.0}, error: `Bridge error: ${error.message}`};
}

async function analyze(request) {
    const response = {sessionId: request.sessionId, language: 'javascript', analyzerVersion: '1.0.0', results: [], vulnerabilities: [], summary: {totalTests: 0, successes: 0, crashes: 0, timeouts: 0, escapes: 0, genuineEscapes: 0, crashRate: 0}};
    try {
        const targetFunc = loadTargetFunction(request.target);
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
                    if (!result.error.includes('Timeout')) genuineEscapes++;
                    response.vulnerabilities.push({input, vulnerabilityType: 'concurrent_escape', severity: 'high', description: `${result.escapeDetails.asyncTasks.length} async resource(s) escaped`, escapeDetails: result.escapeDetails});
                }
            }
        }
        const totalTests = response.results.length;
        response.summary = {totalTests, successes, crashes, timeouts, escapes, genuineEscapes, crashRate: totalTests > 0 ? crashes / totalTests : 0};
    } catch (error) {
        response.summary.crashes = 1;
        response.summary.crashRate = 1.0;
        response.error = error.message;
    }
    return response;
}

async function main() {
    try {
        const chunks = [];
        for await (const chunk of process.stdin) {
            chunks.push(chunk);
        }
        const request = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        const response = await analyze(request);
        console.log(JSON.stringify(response, null, 2));
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify(errorResponse(error)));
        console.error(error.stack);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { analyze, executeTest, loadTargetFunction };
