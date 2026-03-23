package com.escape.analyzer;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.annotations.SerializedName;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class AnalyzerBridge {

    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();
    private static final List<String> RETAINER_HINTS = Arrays.asList(
        "retained", "cache", "audit", "handler", "registry", "store", "sink"
    );
    private static final Set<String> JAVA_KEYWORDS = new HashSet<>(Arrays.asList(
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
        "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
        "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
        "new", "null", "package", "private", "protected", "public", "return", "short", "static", "strictfp",
        "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void", "volatile",
        "while", "true", "false", "var"
    ));
    private static final Pattern IDENTIFIER_PATTERN = Pattern.compile("[A-Za-z_][A-Za-z0-9_]*");
    private static final Pattern RETURN_IDENTIFIER_PATTERN = Pattern.compile("^return\\s+([A-Za-z_][A-Za-z0-9_]*)$");

    static class LoadedTarget {
        Method method;
        String className;
        String methodName;
        String sourceFile;
    }

    static class StaticEscapeFinding {
        String escapeType;
        int line;
        int column;
        String variableName;
        String reason;
        String confidence;
    }

    static class StaticEscapeAnalysis {
        List<StaticEscapeFinding> escapes = new ArrayList<>();
        EscapeDetails details = emptyEscapeDetails();
        String summary = "";

        boolean detected() {
            return !details.escapingReferences.isEmpty();
        }
    }

    static class AssignmentInfo {
        String variable;
        String rhs;
    }

    static class StoreCallInfo {
        String receiver;
        String method;
        String valueExpression;
        boolean isClosure;
    }

    public static void main(String[] args) {
        AnalyzeRequest request = null;
        try {
            // Read request from stdin
            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            StringBuilder requestJson = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                requestJson.append(line);
            }

            // Parse request
            request = gson.fromJson(requestJson.toString(), AnalyzeRequest.class);

            if (request == null) {
                throw new IllegalArgumentException("Empty input: expected JSON request on stdin");
            }

            if (request.target == null || request.target.trim().isEmpty()) {
                throw new IllegalArgumentException("Missing required field: 'target'");
            }

            // Process request
            AnalyzeResponse response = analyze(request);

            // Write response to stdout
            System.out.println(gson.toJson(response));
            System.exit(0);

        } catch (Exception e) {
            // Error response
            String sessionId = (request != null && request.sessionId != null && !request.sessionId.trim().isEmpty())
                ? request.sessionId
                : "unknown";
            AnalyzeResponse errorResponse = buildErrorResponse(sessionId, formatBridgeError(e));

            System.err.println(gson.toJson(errorResponse));
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }

    private static AnalyzeResponse buildErrorResponse(String sessionId, String errorMessage) {
        ErrorDiagnosis diagnosis = diagnoseBridgeError(errorMessage);

        AnalyzeResponse errorResponse = new AnalyzeResponse();
        errorResponse.sessionId = sessionId == null || sessionId.trim().isEmpty() ? "unknown" : sessionId;
        errorResponse.language = "java";
        errorResponse.analyzerVersion = "1.0.0";
        errorResponse.results = new ArrayList<>();
        errorResponse.vulnerabilities = new ArrayList<>();
        errorResponse.summary = new ExecutionSummary();
        errorResponse.summary.totalTests = 0;
        errorResponse.summary.successes = 0;
        errorResponse.summary.crashes = 1;
        errorResponse.summary.timeouts = "Timeout".equals(diagnosis.category) ? 1 : 0;
        errorResponse.summary.escapes = 0;
        errorResponse.summary.genuineEscapes = 0;
        errorResponse.summary.crashRate = 1.0;
        errorResponse.error = errorMessage;
        errorResponse.errorCategory = diagnosis.category;
        errorResponse.suggestedAction = diagnosis.suggestedAction;
        return errorResponse;
    }

    private static String formatBridgeError(Exception e) {
        if (e == null) {
            return "Unknown bridge error";
        }
        String message = e.getMessage();
        String className = e.getClass().getSimpleName();

        if (message == null || message.trim().isEmpty()) {
            return className;
        }

        return className + ": " + message;
    }

    private static ErrorDiagnosis diagnoseBridgeError(String errorMessage) {
        String raw = errorMessage == null ? "" : errorMessage.trim();
        String lower = raw.toLowerCase(Locale.ROOT);

        if (lower.contains("timeout") || lower.contains("timed out") || lower.contains("exceeded")) {
            return new ErrorDiagnosis(
                "Timeout",
                "Inspect blocking operations and missing joins/awaits before increasing timeout."
            );
        }

        if (lower.contains("target resolution")
            || lower.contains("missing required field: 'target'")
            || lower.contains("target loading failed")
            || lower.contains("failed to load")
            || lower.contains("invalid target")
            || lower.contains("target must be")
            || lower.contains("nosuchmethod")
            || lower.contains("module not found")
            || (lower.contains("function") && lower.contains("not found"))) {
            return new ErrorDiagnosis(
                "Target Resolution",
                "Verify target signature/path and ensure the target symbol exists in the selected language module."
            );
        }

        if (lower.contains("protocol/input")
            || lower.contains("invalid json")
            || lower.contains("failed to parse")
            || lower.contains("empty input")
            || lower.contains("expected json")
            || lower.contains("jsonsyntaxexception")
            || lower.contains("eofexception")
            || lower.contains("end of input")
            || lower.contains("json")
            || lower.contains("parse")
            || lower.contains("stdin")
            || lower.contains("protocol")) {
            return new ErrorDiagnosis(
                "Protocol/Input",
                "Validate request JSON and ensure bridge stdin/stdout protocol fields match the orchestrator contract."
            );
        }

        if (lower.contains("environment")
            || lower.contains("permission denied")
            || lower.contains("not available")
            || lower.contains("not found in path")
            || lower.contains("command not found")
            || lower.contains("missing tools")
            || lower.contains("java not found")) {
            return new ErrorDiagnosis(
                "Environment",
                "Check runtime/toolchain installation and PATH configuration for the selected language analyzer."
            );
        }

        if (lower.contains("runtime crash")
            || lower.contains("panic")
            || lower.contains("exception")
            || lower.contains("traceback")
            || lower.contains("segmentation")) {
            return new ErrorDiagnosis(
                "Runtime Crash",
                "Re-run with --verbose and inspect bridge stack traces for runtime exceptions."
            );
        }

        return new ErrorDiagnosis(
            "Unknown",
            "Re-run with --verbose and inspect bridge stdout/stderr for additional diagnostics."
        );
    }

    private static AnalyzeResponse analyze(AnalyzeRequest request) throws Exception {
        AnalyzeResponse response = new AnalyzeResponse();
        response.sessionId = request.sessionId;
        response.language = "java";
        response.analyzerVersion = "1.0.0";
        response.results = new ArrayList<>();
        response.vulnerabilities = new ArrayList<>();

        // Load target method
        LoadedTarget target = loadTargetMethod(request.target);
        StaticEscapeAnalysis staticAnalysis = runTraditionalStaticEscapeAnalysis(target.sourceFile, target.methodName);

        // Run tests
        int successes = 0, crashes = 0, timeouts = 0, escapes = 0, genuineEscapes = 0;

        List<String> inputs = request.inputs;
        if (inputs == null || inputs.isEmpty()) {
            inputs = Collections.singletonList("");
        }

        for (String input : inputs) {
            for (int i = 0; i < request.repeat; i++) {
                ExecutionResult result = executeTest(target.method, input, request.timeoutSeconds);

                if (staticAnalysis.detected()) {
                    result.escapeDetected = true;
                    result.escapeDetails = mergeEscapeDetails(result.escapeDetails, staticAnalysis.details);
                }

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
                    int staticCount = result.escapeDetails.escapingReferences.size();
                    int threadCount = result.escapeDetails.threads.size();
                    String description = result.escapeDetails.summary();
                    if (staticCount > 0) {
                        description = staticCount + " static object escape(s) detected";
                        if (staticAnalysis.summary != null && !staticAnalysis.summary.isEmpty()) {
                            description = description + " (" + staticAnalysis.summary + ")";
                        }
                        if (threadCount > 0) {
                            description = description + " + " + threadCount + " thread leak(s)";
                        }
                    }
                    vuln.description = description;
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

    private static LoadedTarget loadTargetMethod(String target) throws Exception {
        // Parse target from right to left so Windows paths/classpaths remain intact.
        int lastColon = target.lastIndexOf(':');
        if (lastColon <= 0 || lastColon == target.length() - 1) {
            throw new IllegalArgumentException("Target must be ClassName:methodName or jar:ClassName:methodName");
        }

        int secondLastColon = target.lastIndexOf(':', lastColon - 1);

        String className;
        String methodName = target.substring(lastColon + 1).trim();
        Method method;
        String sourceFile = null;

        if (secondLastColon > 0) {
            // Load from classpath (jar and/or classes directory)
            String classPathSpec = target.substring(0, secondLastColon).trim();
            className = target.substring(secondLastColon + 1, lastColon).trim();
            if (classPathSpec.isEmpty() || className.isEmpty() || methodName.isEmpty()) {
                throw new IllegalArgumentException("Invalid target format: " + target);
            }

            String[] entries = classPathSpec.split(Pattern.quote(File.pathSeparator));
            List<URL> urls = new ArrayList<>();
            for (String entry : entries) {
                String trimmed = entry.trim();
                if (!trimmed.isEmpty()) {
                    urls.add(new File(trimmed).toURI().toURL());
                }
            }
            if (urls.isEmpty()) {
                throw new IllegalArgumentException("No classpath entries in target: " + target);
            }

            // Note: URLClassLoader is intentionally not closed here because the loaded
            // class and method must remain accessible after this method returns.
            // The classloader will be garbage collected when no longer referenced.
            @SuppressWarnings("resource")
            URLClassLoader classLoader = new URLClassLoader(urls.toArray(new URL[0]));
            Class<?> clazz = classLoader.loadClass(className);
            method = findMethodByName(clazz, methodName);
            sourceFile = resolveSourceFile(className);
        } else {
            className = target.substring(0, lastColon).trim();
            if (className.isEmpty() || methodName.isEmpty()) {
                throw new IllegalArgumentException("Invalid target format: " + target);
            }
            Class<?> clazz = Class.forName(className);
            method = findMethodByName(clazz, methodName);
            sourceFile = resolveSourceFile(className);
        }

        LoadedTarget loadedTarget = new LoadedTarget();
        loadedTarget.method = method;
        loadedTarget.className = className;
        loadedTarget.methodName = methodName;
        loadedTarget.sourceFile = sourceFile;
        return loadedTarget;
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
        EscapeDetails escapeDetails = emptyEscapeDetails();

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

    private static String resolveSourceFile(String className) {
        if (className == null || className.trim().isEmpty()) {
            return null;
        }

        String relative = className.replace('.', File.separatorChar) + ".java";
        Path cwd = Paths.get(System.getProperty("user.dir"));
        List<Path> candidates = Arrays.asList(
            cwd.resolve(relative),
            cwd.resolve("tests").resolve("java").resolve("src").resolve("main").resolve("java").resolve(relative),
            cwd.resolve("src").resolve("main").resolve("java").resolve(relative)
        );

        for (Path candidate : candidates) {
            if (Files.exists(candidate)) {
                return candidate.toAbsolutePath().normalize().toString();
            }
        }

        return null;
    }

    private static EscapeDetails emptyEscapeDetails() {
        EscapeDetails details = new EscapeDetails();
        details.escapingReferences = new ArrayList<>();
        details.escapePaths = new ArrayList<>();
        details.threads = new ArrayList<>();
        details.processes = new ArrayList<>();
        details.asyncTasks = new ArrayList<>();
        details.goroutines = new ArrayList<>();
        details.other = new ArrayList<>();
        return details;
    }

    private static EscapeDetails mergeEscapeDetails(EscapeDetails primary, EscapeDetails secondary) {
        EscapeDetails merged = emptyEscapeDetails();

        EscapeDetails first = primary == null ? emptyEscapeDetails() : primary;
        EscapeDetails second = secondary == null ? emptyEscapeDetails() : secondary;

        merged.escapingReferences.addAll(first.escapingReferences);
        merged.escapingReferences.addAll(second.escapingReferences);

        merged.escapePaths.addAll(first.escapePaths);
        merged.escapePaths.addAll(second.escapePaths);

        merged.threads.addAll(first.threads);
        merged.threads.addAll(second.threads);

        merged.processes.addAll(first.processes);
        merged.processes.addAll(second.processes);

        merged.asyncTasks.addAll(first.asyncTasks);
        merged.asyncTasks.addAll(second.asyncTasks);

        merged.goroutines.addAll(first.goroutines);
        merged.goroutines.addAll(second.goroutines);

        merged.other.addAll(first.other);
        merged.other.addAll(second.other);

        return merged;
    }

    private static StaticEscapeAnalysis runTraditionalStaticEscapeAnalysis(String sourceFile, String methodName) {
        StaticEscapeAnalysis analysis = new StaticEscapeAnalysis();
        if (sourceFile == null || sourceFile.trim().isEmpty() || methodName == null || methodName.trim().isEmpty()) {
            return analysis;
        }

        List<String> lines;
        try {
            lines = Files.readAllLines(Paths.get(sourceFile));
        } catch (IOException e) {
            return analysis;
        }

        Set<String> retainers = collectClassRetainers(lines);
        Set<String> localVars = new HashSet<>();
        Set<String> localObjectVars = new HashSet<>();
        Map<String, Set<String>> dependencies = new HashMap<>();
        Set<String> dedupe = new HashSet<>();

        boolean inTarget = false;
        int braceDepth = 0;

        for (int idx = 0; idx < lines.size(); idx++) {
            String stripped = stripInlineComment(lines.get(idx)).trim();

            if (!inTarget) {
                String detectedMethod = extractMethodName(stripped);
                if (detectedMethod != null && detectedMethod.equals(methodName)) {
                    inTarget = true;
                    braceDepth = countBraces(stripped);
                    if (braceDepth <= 0) {
                        braceDepth = 1;
                    }
                }
                continue;
            }

            AssignmentInfo assignment = extractAssignment(stripped);
            if (assignment != null) {
                localVars.add(assignment.variable);
                if (looksLikeObjectInitializer(assignment.rhs)) {
                    localObjectVars.add(assignment.variable);
                }
                for (String id : extractIdentifiers(assignment.rhs)) {
                    if (id.equals(assignment.variable)) {
                        continue;
                    }
                    if (localVars.contains(id) || localObjectVars.contains(id)) {
                        dependencies.computeIfAbsent(assignment.variable, key -> new HashSet<>()).add(id);
                    }
                }
            }

            StoreCallInfo storeCall = extractStoreCall(stripped);
            if (storeCall != null) {
                if (localObjectVars.contains(storeCall.receiver)) {
                    for (String id : extractIdentifiers(storeCall.valueExpression)) {
                        if (localVars.contains(id) || localObjectVars.contains(id)) {
                            dependencies.computeIfAbsent(storeCall.receiver, key -> new HashSet<>()).add(id);
                        }
                    }
                }

                if (isRetainerContainer(storeCall.receiver, retainers)) {
                    Set<String> escapedVars = resolveEscapedVariables(
                        storeCall.valueExpression,
                        localVars,
                        localObjectVars,
                        dependencies
                    );

                    for (String escapedVar : escapedVars) {
                        String escapeType = storeCall.isClosure ? "closure" : "global";
                        String reason = storeCall.isClosure
                            ? "Local object '" + escapedVar + "' captured by retained closure in '" + storeCall.receiver + "." + storeCall.method + "'"
                            : "Local object '" + escapedVar + "' stored in retained class container '" + storeCall.receiver + "'";
                        addStaticFinding(
                            analysis.escapes,
                            dedupe,
                            escapeType,
                            idx + 1,
                            Math.max(stripped.indexOf(storeCall.receiver), 0),
                            escapedVar,
                            reason,
                            "high"
                        );
                    }
                }
            }

            String returned = extractReturnIdentifier(stripped);
            if (returned != null && (localObjectVars.contains(returned) || dependencies.containsKey(returned))) {
                String reason = "Local object '" + returned + "' returned from method";
                addStaticFinding(
                    analysis.escapes,
                    dedupe,
                    "return",
                    idx + 1,
                    Math.max(stripped.indexOf(returned), 0),
                    returned,
                    reason,
                    "high"
                );
            }

            braceDepth += countBraces(stripped);
            if (braceDepth <= 0) {
                break;
            }
        }

        for (StaticEscapeFinding finding : analysis.escapes) {
            ObjectReference reference = new ObjectReference();
            reference.variableName = finding.variableName;
            reference.objectType = "unknown";
            reference.allocationSite = sourceFile + ":" + finding.line + ":" + finding.column;
            reference.escapedVia = finding.escapeType;
            analysis.details.escapingReferences.add(reference);

            EscapePath path = new EscapePath();
            path.source = finding.variableName;
            path.destination = escapeDestination(finding.escapeType);
            path.escapeType = finding.escapeType;
            path.confidence = finding.confidence;
            analysis.details.escapePaths.add(path);
        }

        analysis.summary = summarizeStaticFindings(analysis.escapes);
        return analysis;
    }

    private static Set<String> collectClassRetainers(List<String> lines) {
        Set<String> retainers = new HashSet<>();

        for (String rawLine : lines) {
            String stripped = stripInlineComment(rawLine).trim();
            if (!stripped.contains("static") || !stripped.contains("=")) {
                continue;
            }

            int assignIdx = stripped.indexOf('=');
            if (assignIdx <= 0) {
                continue;
            }
            String left = stripped.substring(0, assignIdx).trim();
            String rhs = stripped.substring(assignIdx + 1).trim();
            String name = extractLastIdentifier(left);
            if (name == null) {
                continue;
            }

            if (isRetainerName(name) && looksLikeRetainerInitializer(rhs)) {
                retainers.add(name);
            }
        }

        return retainers;
    }

    private static boolean isRetainerName(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        for (String hint : RETAINER_HINTS) {
            if (lower.contains(hint)) {
                return true;
            }
        }
        return false;
    }

    private static boolean looksLikeRetainerInitializer(String rhs) {
        String normalized = rhs.trim().toLowerCase(Locale.ROOT);
        return normalized.startsWith("new arraylist")
            || normalized.startsWith("new linkedlist")
            || normalized.startsWith("new hashmap")
            || normalized.startsWith("new map")
            || normalized.startsWith("new hashset")
            || normalized.startsWith("new set")
            || normalized.startsWith("new concurrent");
    }

    private static boolean looksLikeObjectInitializer(String rhs) {
        String normalized = rhs.trim().toLowerCase(Locale.ROOT);
        return normalized.startsWith("new ") || normalized.startsWith("{");
    }

    private static boolean isRetainerContainer(String receiver, Set<String> retainers) {
        return retainers.contains(receiver) || isRetainerName(receiver);
    }

    private static AssignmentInfo extractAssignment(String line) {
        String trimmed = line.trim();
        if (trimmed.isEmpty() || trimmed.startsWith("return ")) {
            return null;
        }
        if (trimmed.startsWith("if ") || trimmed.startsWith("for ") || trimmed.startsWith("while ")) {
            return null;
        }
        if (trimmed.contains("==")) {
            return null;
        }

        String normalized = trimmed.endsWith(";") ? trimmed.substring(0, trimmed.length() - 1).trim() : trimmed;
        int assignIdx = normalized.indexOf('=');
        if (assignIdx <= 0) {
            return null;
        }

        String left = normalized.substring(0, assignIdx).trim();
        if (left.contains("(")) {
            return null;
        }

        String rhs = normalized.substring(assignIdx + 1).trim();
        if (rhs.isEmpty()) {
            return null;
        }

        String variable = extractLastIdentifier(left);
        if (variable == null) {
            return null;
        }

        AssignmentInfo info = new AssignmentInfo();
        info.variable = variable;
        info.rhs = rhs;
        return info;
    }

    private static StoreCallInfo extractStoreCall(String line) {
        String trimmed = line.trim();
        String normalized = trimmed.endsWith(";") ? trimmed.substring(0, trimmed.length() - 1).trim() : trimmed;
        int dotIdx = normalized.indexOf('.');
        int openIdx = normalized.indexOf('(');
        int closeIdx = normalized.lastIndexOf(')');
        if (dotIdx <= 0 || openIdx <= dotIdx || closeIdx <= openIdx) {
            return null;
        }

        String receiver = extractLastIdentifier(normalized.substring(0, dotIdx).trim());
        if (receiver == null) {
            return null;
        }

        String method = normalized.substring(dotIdx + 1, openIdx).trim();
        if (!("put".equals(method) || "add".equals(method) || "offer".equals(method) || "push".equals(method) || "set".equals(method))) {
            return null;
        }

        String args = normalized.substring(openIdx + 1, closeIdx).trim();
        if (args.isEmpty()) {
            return null;
        }

        String valueExpression = args;
        if ("put".equals(method) || "set".equals(method)) {
            String[] parts = splitFirstTopLevelComma(args);
            if (parts != null) {
                valueExpression = parts[1].trim();
            }
        }

        StoreCallInfo info = new StoreCallInfo();
        info.receiver = receiver;
        info.method = method;
        info.valueExpression = valueExpression;
        info.isClosure = valueExpression.contains("->") || valueExpression.contains("::");
        return info;
    }

    private static String extractReturnIdentifier(String line) {
        String normalized = line.trim();
        if (normalized.endsWith(";")) {
            normalized = normalized.substring(0, normalized.length() - 1).trim();
        }
        Matcher matcher = RETURN_IDENTIFIER_PATTERN.matcher(normalized);
        if (!matcher.matches()) {
            return null;
        }
        return matcher.group(1);
    }

    private static String extractLastIdentifier(String text) {
        List<String> ids = extractIdentifiers(text);
        if (ids.isEmpty()) {
            return null;
        }
        return ids.get(ids.size() - 1);
    }

    private static List<String> extractIdentifiers(String text) {
        List<String> ids = new ArrayList<>();
        Matcher matcher = IDENTIFIER_PATTERN.matcher(text);
        while (matcher.find()) {
            String candidate = matcher.group();
            if (!JAVA_KEYWORDS.contains(candidate)) {
                ids.add(candidate);
            }
        }
        return ids;
    }

    private static Set<String> resolveEscapedVariables(
        String expression,
        Set<String> localVars,
        Set<String> localObjectVars,
        Map<String, Set<String>> dependencies
    ) {
        Set<String> escaped = new HashSet<>();
        for (String id : extractIdentifiers(expression)) {
            if (localVars.contains(id) || localObjectVars.contains(id)) {
                escaped.add(id);
                expandDependencies(id, dependencies, escaped, new HashSet<>());
            }
        }
        return escaped;
    }

    private static void expandDependencies(
        String variable,
        Map<String, Set<String>> dependencies,
        Set<String> output,
        Set<String> visited
    ) {
        if (visited.contains(variable)) {
            return;
        }
        visited.add(variable);

        Set<String> next = dependencies.get(variable);
        if (next == null) {
            return;
        }

        for (String dep : next) {
            if (output.add(dep)) {
                expandDependencies(dep, dependencies, output, visited);
            }
        }
    }

    private static String summarizeStaticFindings(List<StaticEscapeFinding> findings) {
        if (findings == null || findings.isEmpty()) {
            return "";
        }

        List<String> parts = new ArrayList<>();
        for (StaticEscapeFinding finding : findings) {
            parts.add(finding.escapeType + ":" + finding.variableName + "@L" + finding.line);
        }
        return String.join("; ", parts);
    }

    private static void addStaticFinding(
        List<StaticEscapeFinding> findings,
        Set<String> dedupe,
        String escapeType,
        int line,
        int column,
        String variableName,
        String reason,
        String confidence
    ) {
        String key = escapeType + "|" + line + "|" + variableName + "|" + reason;
        if (dedupe.contains(key)) {
            return;
        }
        dedupe.add(key);

        StaticEscapeFinding finding = new StaticEscapeFinding();
        finding.escapeType = escapeType;
        finding.line = line;
        finding.column = Math.max(column, 0);
        finding.variableName = variableName;
        finding.reason = reason;
        finding.confidence = confidence;
        findings.add(finding);
    }

    private static String[] splitFirstTopLevelComma(String text) {
        int parenDepth = 0;
        int braceDepth = 0;
        int bracketDepth = 0;

        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            switch (ch) {
                case '(':
                    parenDepth++;
                    break;
                case ')':
                    parenDepth--;
                    break;
                case '{':
                    braceDepth++;
                    break;
                case '}':
                    braceDepth--;
                    break;
                case '[':
                    bracketDepth++;
                    break;
                case ']':
                    bracketDepth--;
                    break;
                case ',':
                    if (parenDepth == 0 && braceDepth == 0 && bracketDepth == 0) {
                        return new String[] {text.substring(0, i), text.substring(i + 1)};
                    }
                    break;
                default:
                    break;
            }
        }

        return null;
    }

    private static int countBraces(String text) {
        int depth = 0;
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (ch == '{') {
                depth++;
            } else if (ch == '}') {
                depth--;
            }
        }
        return depth;
    }

    private static String stripInlineComment(String line) {
        int idx = line.indexOf("//");
        if (idx >= 0) {
            return line.substring(0, idx);
        }
        return line;
    }

    private static String extractMethodName(String line) {
        String trimmed = line.trim();
        if (!trimmed.contains("(") || trimmed.contains("=") || trimmed.startsWith("if ")
            || trimmed.startsWith("for ") || trimmed.startsWith("while ")) {
            return null;
        }

        int openIdx = trimmed.indexOf('(');
        if (openIdx <= 0) {
            return null;
        }

        String before = trimmed.substring(0, openIdx).trim();
        if (before.isEmpty()) {
            return null;
        }

        String[] parts = before.split("\\s+");
        if (parts.length < 2) {
            return null;
        }

        String candidate = parts[parts.length - 1];
        for (int i = 0; i < candidate.length(); i++) {
            char ch = candidate.charAt(i);
            if (!Character.isLetterOrDigit(ch) && ch != '_') {
                return null;
            }
        }

        return candidate;
    }

    private static String escapeDestination(String escapeType) {
        if ("return".equals(escapeType)) {
            return "caller";
        }
        if ("parameter".equals(escapeType)) {
            return "callee";
        }
        if ("global".equals(escapeType)) {
            return "module_scope";
        }
        if ("closure".equals(escapeType)) {
            return "closure_scope";
        }
        return "heap_container";
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
        String error;
        @SerializedName("error_category")
        String errorCategory;
        @SerializedName("suggested_action")
        String suggestedAction;
    }

    static class ErrorDiagnosis {
        String category;
        String suggestedAction;

        ErrorDiagnosis(String category, String suggestedAction) {
            this.category = category;
            this.suggestedAction = suggestedAction;
        }
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
        List<ObjectReference> escapingReferences;
        List<EscapePath> escapePaths;
        List<ThreadEscape> threads;
        List<ProcessEscape> processes;
        List<AsyncTaskEscape> asyncTasks;
        List<GoroutineEscape> goroutines;
        List<String> other;

        String summary() {
            List<String> parts = new ArrayList<>();
            if (!escapingReferences.isEmpty()) parts.add(escapingReferences.size() + " static object escape(s)");
            if (!threads.isEmpty()) parts.add(threads.size() + " thread(s)");
            if (!processes.isEmpty()) parts.add(processes.size() + " process(es)");
            if (!asyncTasks.isEmpty()) parts.add(asyncTasks.size() + " async task(s)");
            return String.join(", ", parts);
        }
    }

    static class ObjectReference {
        String variableName;
        String objectType;
        String allocationSite;
        String escapedVia;
    }

    static class EscapePath {
        String source;
        String destination;
        String escapeType;
        String confidence;
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
