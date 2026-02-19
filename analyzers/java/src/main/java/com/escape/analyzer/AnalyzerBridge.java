package com.escape.analyzer;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.*;

public class AnalyzerBridge {

    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    public static void main(String[] args) {
        try {
            // Read request from stdin
            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            StringBuilder requestJson = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                requestJson.append(line);
            }

            // Parse request
            AnalyzeRequest request = gson.fromJson(requestJson.toString(), AnalyzeRequest.class);

            // Process request
            AnalyzeResponse response = analyze(request);

            // Write response to stdout
            System.out.println(gson.toJson(response));
            System.exit(0);

        } catch (Exception e) {
            // Error response
            AnalyzeResponse errorResponse = new AnalyzeResponse();
            errorResponse.sessionId = "unknown";
            errorResponse.language = "java";
            errorResponse.analyzerVersion = "1.0.0";
            errorResponse.results = new ArrayList<>();
            errorResponse.vulnerabilities = new ArrayList<>();
            errorResponse.summary = new ExecutionSummary();
            errorResponse.summary.totalTests = 0;
            errorResponse.summary.crashes = 1;
            errorResponse.summary.crashRate = 1.0;

            System.err.println(gson.toJson(errorResponse));
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }

    private static AnalyzeResponse analyze(AnalyzeRequest request) throws Exception {
        AnalyzeResponse response = new AnalyzeResponse();
        response.sessionId = request.sessionId;
        response.language = "java";
        response.analyzerVersion = "1.0.0";
        response.results = new ArrayList<>();
        response.vulnerabilities = new ArrayList<>();

        // Load target method
        Method targetMethod = loadTargetMethod(request.target);

        // Run tests
        int successes = 0, crashes = 0, timeouts = 0, escapes = 0, genuineEscapes = 0;

        for (String input : request.inputs) {
            for (int i = 0; i < request.repeat; i++) {
                ExecutionResult result = executeTest(targetMethod, input, request.timeoutSeconds);
                response.results.add(result);

                if (result.success) successes++;
                if (result.crashed) crashes++;
                if (result.error.contains("timeout")) timeouts++;
                if (result.escapeDetected) {
                    escapes++;
                    if (!result.error.contains("timeout")) {
                        genuineEscapes++;
                    }

                    // Add vulnerability
                    Vulnerability vuln = new Vulnerability();
                    vuln.input = input;
                    vuln.vulnerabilityType = "concurrent_escape";
                    vuln.severity = "high";
                    vuln.description = result.escapeDetails.summary();
                    vuln.escapeDetails = result.escapeDetails;
                    response.vulnerabilities.add(vuln);
                }
            }
        }

        // Summary
        int totalTests = response.results.size();
        ExecutionSummary summary = new ExecutionSummary();
        summary.totalTests = totalTests;
        summary.successes = successes;
        summary.crashes = crashes;
        summary.timeouts = timeouts;
        summary.escapes = escapes;
        summary.genuineEscapes = genuineEscapes;
        summary.crashRate = totalTests > 0 ? (double) crashes / totalTests : 0.0;
        response.summary = summary;

        return response;
    }

    private static Method loadTargetMethod(String target) throws Exception {
        // Parse target: ClassName:methodName or file.jar:ClassName:methodName
        String[] parts = target.split(":");
        if (parts.length < 2) {
            throw new IllegalArgumentException("Target must be ClassName:methodName or jar:ClassName:methodName");
        }

        String className, methodName;
        if (parts.length == 3) {
            // Load from JAR
            String jarPath = parts[0];
            className = parts[1];
            methodName = parts[2];
            URL jarUrl = new File(jarPath).toURI().toURL();
            URLClassLoader classLoader = new URLClassLoader(new URL[]{jarUrl});
            Class<?> clazz = classLoader.loadClass(className);
            return findMethodByName(clazz, methodName);
        } else {
            className = parts[0];
            methodName = parts[1];
            Class<?> clazz = Class.forName(className);
            return findMethodByName(clazz, methodName);
        }
    }

    private static Method findMethodByName(Class<?> clazz, String methodName) throws NoSuchMethodException {
        for (Method method : clazz.getDeclaredMethods()) {
            if (method.getName().equals(methodName)) {
                method.setAccessible(true);
                return method;
            }
        }
        throw new NoSuchMethodException(methodName + " in " + clazz.getName());
    }

    private static ExecutionResult executeTest(Method method, String input, double timeoutSeconds) {
        ExecutionResult result = new ExecutionResult();
        result.inputData = input;
        result.success = false;
        result.crashed = false;
        result.escapeDetected = false;

        // Capture baseline thread state
        ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
        Map<Long, ThreadInfo> baselineThreads = getAllThreadInfo(threadMXBean);

        long startTime = System.currentTimeMillis();

        try {
            // Invoke method in a timeout-aware manner
            Thread testThread = new Thread(() -> {
                try {
                    Object returnValue = method.invoke(null, input);
                    result.output = String.valueOf(returnValue);
                    result.success = true;
                } catch (Exception e) {
                    result.crashed = true;
                    result.error = e.getClass().getSimpleName() + ": " + e.getMessage();
                }
            });
            testThread.setDaemon(false);
            testThread.start();

            // Wait with timeout
            testThread.join((long)(timeoutSeconds * 1000));
            if (testThread.isAlive()) {
                result.crashed = true;
                result.error = "Timeout exceeded";
            }

        } catch (Exception e) {
            result.crashed = true;
            result.error = e.getClass().getSimpleName() + ": " + e.getMessage();
        }

        long executionTime = System.currentTimeMillis() - startTime;
        result.executionTimeMs = executionTime;

        // Wait for async operations to settle
        try {
            Thread.sleep(100);
        } catch (InterruptedException ignored) {
        }

        // Check for escaped threads (with detailed info)
        Map<Long, ThreadInfo> currentThreads = getAllThreadInfo(threadMXBean);
        EscapeDetails escapeDetails = new EscapeDetails();
        escapeDetails.threads = new ArrayList<>();
        escapeDetails.processes = new ArrayList<>();
        escapeDetails.asyncTasks = new ArrayList<>();
        escapeDetails.goroutines = new ArrayList<>();
        escapeDetails.other = new ArrayList<>();

        // Detect new threads (excluding system/JVM threads)
        Set<String> systemPrefixes = new HashSet<>(Arrays.asList(
            "ForkJoinPool", "Common-ForkJoin", "Attach Listener", "Service Thread",
            "Reference Handler", "Finalizer", "Signal Dispatcher", "Sweeper thread",
            "AWT", "AppKit", "GC task thread"
        ));

        for (Long threadId : currentThreads.keySet()) {
            if (!baselineThreads.containsKey(threadId)) {
                ThreadInfo info = currentThreads.get(threadId);
                if (info != null && !isSystemThread(info, systemPrefixes)) {
                    ThreadEscape threadEscape = new ThreadEscape();
                    threadEscape.threadId = String.valueOf(threadId);
                    threadEscape.name = info.getThreadName();
                    threadEscape.isDaemon = info.isDaemon();
                    threadEscape.state = info.getThreadState().toString();

                    // Capture stack trace for escaped threads
                    StackTraceElement[] stackTrace = info.getStackTrace();
                    threadEscape.stackTrace = new ArrayList<>();
                    for (StackTraceElement element : stackTrace) {
                        threadEscape.stackTrace.add(element.toString());
                    }

                    escapeDetails.threads.add(threadEscape);
                }
            }
        }

        // Check if any threads changed state from running to blocked (potential deadlock)
        for (Long threadId : baselineThreads.keySet()) {
            if (currentThreads.containsKey(threadId)) {
                ThreadInfo baseline = baselineThreads.get(threadId);
                ThreadInfo current = currentThreads.get(threadId);
                if (baseline.getThreadState() != current.getThreadState() &&
                    current.getThreadState().toString().equals("BLOCKED")) {
                    escapeDetails.other.add("thread_blocked:" + baseline.getThreadName() + ":" + threadId);
                }
            }
        }

        result.escapeDetected = !escapeDetails.threads.isEmpty();
        result.escapeDetails = escapeDetails;

        return result;
    }

    private static boolean isSystemThread(ThreadInfo info, Set<String> systemPrefixes) {
        String name = info.getThreadName();
        for (String prefix : systemPrefixes) {
            if (name.startsWith(prefix)) return true;
        }
        return false;
    }

    private static Map<Long, ThreadInfo> getAllThreadInfo(ThreadMXBean threadMXBean) {
        Map<Long, ThreadInfo> threads = new HashMap<>();
        long[] ids = threadMXBean.getAllThreadIds();
        ThreadInfo[] infos = threadMXBean.getThreadInfo(ids, Integer.MAX_VALUE);
        for (ThreadInfo info : infos) {
            if (info != null) {
                threads.put(info.getThreadId(), info);
            }
        }
        return threads;
    }



    // Protocol classes (matching Rust protocol)
    static class AnalyzeRequest {
        String sessionId;
        String target;
        List<String> inputs;
        int repeat;
        double timeoutSeconds;
        Map<String, String> options;
    }

    static class AnalyzeResponse {
        String sessionId;
        String language;
        String analyzerVersion;
        List<ExecutionResult> results;
        List<Vulnerability> vulnerabilities;
        ExecutionSummary summary;
    }

    static class ExecutionResult {
        String inputData;
        boolean success;
        boolean crashed;
        String output = "";
        String error = "";
        long executionTimeMs;
        boolean escapeDetected;
        EscapeDetails escapeDetails;
    }

    static class EscapeDetails {
        List<ThreadEscape> threads;
        List<ProcessEscape> processes;
        List<AsyncTaskEscape> asyncTasks;
        List<GoroutineEscape> goroutines;
        List<String> other;

        String summary() {
            List<String> parts = new ArrayList<>();
            if (!threads.isEmpty()) parts.add(threads.size() + " thread(s)");
            if (!processes.isEmpty()) parts.add(processes.size() + " process(es)");
            if (!asyncTasks.isEmpty()) parts.add(asyncTasks.size() + " async task(s)");
            return String.join(", ", parts);
        }
    }

    static class ThreadEscape {
        String threadId;
        String name;
        boolean isDaemon;
        String state;
        List<String> stackTrace;
    }

    static class ProcessEscape {
        int pid;
        String name;
        String cmdline;
    }

    static class AsyncTaskEscape {
        String taskId;
        String taskType;
        String state;
    }

    static class GoroutineEscape {
        long goroutineId;
        String state;
        String function;
    }

    static class Vulnerability {
        String input;
        String vulnerabilityType;
        String severity;
        String description;
        EscapeDetails escapeDetails;
    }

    static class ExecutionSummary {
        int totalTests;
        int successes;
        int crashes;
        int timeouts;
        int escapes;
        int genuineEscapes;
        double crashRate;
    }
}
