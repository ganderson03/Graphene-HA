package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
)

var temporaryTargetDirs []string

var goRetainerHints = []string{"retained", "cache", "audit", "handler", "registry", "store", "sink"}
var goIdentifierRegex = regexp.MustCompile(`[A-Za-z_][A-Za-z0-9_]*`)
var goReturnIdentifierRegex = regexp.MustCompile(`^return\s+([A-Za-z_][A-Za-z0-9_]*)$`)
var goKeywords = map[string]struct{}{
	"break": {}, "case": {}, "chan": {}, "const": {}, "continue": {}, "default": {},
	"defer": {}, "else": {}, "fallthrough": {}, "for": {}, "func": {}, "go": {},
	"goto": {}, "if": {}, "import": {}, "interface": {}, "map": {}, "package": {},
	"range": {}, "return": {}, "select": {}, "struct": {}, "switch": {}, "type": {},
	"var": {}, "true": {}, "false": {}, "nil": {}, "string": {}, "int": {},
	"bool": {}, "any": {}, "append": {}, "make": {},
}

// Protocol structures matching Rust protocol
type AnalyzeRequest struct {
	SessionID      string            `json:"session_id"`
	Target         string            `json:"target"`
	Inputs         []string          `json:"inputs"`
	Repeat         int               `json:"repeat"`
	TimeoutSeconds float64           `json:"timeout_seconds"`
	Options        map[string]string `json:"options"`
}

type AnalyzeResponse struct {
	SessionID       string            `json:"session_id"`
	Language        string            `json:"language"`
	AnalyzerVersion string            `json:"analyzer_version"`
	Results         []ExecutionResult `json:"results"`
	Vulnerabilities []Vulnerability   `json:"vulnerabilities"`
	Summary         ExecutionSummary  `json:"summary"`
	Error           string            `json:"error,omitempty"`
	ErrorCategory   string            `json:"error_category,omitempty"`
	SuggestedAction string            `json:"suggested_action,omitempty"`
}

type ErrorDiagnosis struct {
	Category        string
	SuggestedAction string
}

type ExecutionResult struct {
	InputData       string        `json:"input_data"`
	Success         bool          `json:"success"`
	Crashed         bool          `json:"crashed"`
	Output          string        `json:"output"`
	Error           string        `json:"error"`
	ExecutionTimeMs int64         `json:"execution_time_ms"`
	EscapeDetected  bool          `json:"escape_detected"`
	EscapeDetails   EscapeDetails `json:"escape_details"`
}

type EscapeDetails struct {
	EscapingReferences []ObjectReference `json:"escaping_references"`
	EscapePaths        []EscapePath      `json:"escape_paths"`
	Threads            []ThreadEscape    `json:"threads"`
	Processes          []ProcessEscape   `json:"processes"`
	AsyncTasks         []AsyncTaskEscape `json:"async_tasks"`
	Goroutines         []GoroutineEscape `json:"goroutines"`
	Other              []string          `json:"other"`
}

type ObjectReference struct {
	VariableName   string `json:"variable_name"`
	ObjectType     string `json:"object_type"`
	AllocationSite string `json:"allocation_site"`
	EscapedVia     string `json:"escaped_via"`
}

type EscapePath struct {
	Source      string `json:"source"`
	Destination string `json:"destination"`
	EscapeType  string `json:"escape_type"`
	Confidence  string `json:"confidence"`
}

type StaticEscapeFinding struct {
	EscapeType   string
	Line         int
	Column       int
	VariableName string
	Reason       string
	Confidence   string
}

type ThreadEscape struct {
	ThreadID   string   `json:"thread_id"`
	Name       string   `json:"name"`
	IsDaemon   bool     `json:"is_daemon"`
	State      string   `json:"state"`
	StackTrace []string `json:"stack_trace"`
}

type ProcessEscape struct {
	PID     int    `json:"pid"`
	Name    string `json:"name"`
	Cmdline string `json:"cmdline"`
}

type AsyncTaskEscape struct {
	TaskID   string `json:"task_id"`
	TaskType string `json:"task_type"`
	State    string `json:"state"`
}

type GoroutineEscape struct {
	GoroutineID uint64 `json:"goroutine_id"`
	State       string `json:"state"`
	Function    string `json:"function"`
}

type Vulnerability struct {
	Input             string        `json:"input"`
	VulnerabilityType string        `json:"vulnerability_type"`
	Severity          string        `json:"severity"`
	Description       string        `json:"description"`
	EscapeDetails     EscapeDetails `json:"escape_details"`
}

type ExecutionSummary struct {
	TotalTests     int     `json:"total_tests"`
	Successes      int     `json:"successes"`
	Crashes        int     `json:"crashes"`
	Timeouts       int     `json:"timeouts"`
	Escapes        int     `json:"escapes"`
	GenuineEscapes int     `json:"genuine_escapes"`
	CrashRate      float64 `json:"crash_rate"`
}

func main() {
	// Read request from stdin
	requestBytes, err := io.ReadAll(os.Stdin)
	if err != nil {
		errorResponse(fmt.Sprintf("Failed to read stdin: %v", err))
		return
	}

	var request AnalyzeRequest
	if err := json.Unmarshal(requestBytes, &request); err != nil {
		errorResponse(fmt.Sprintf("Failed to parse request: %v", err))
		return
	}

	defer cleanupTemporaryTargets()

	// Process request
	response := analyze(request)

	// Write response to stdout
	responseBytes, _ := json.MarshalIndent(response, "", "  ")
	fmt.Println(string(responseBytes))
}

func analyze(request AnalyzeRequest) AnalyzeResponse {
	response := AnalyzeResponse{
		SessionID:       request.SessionID,
		Language:        "go",
		AnalyzerVersion: "1.0.0",
		Results:         []ExecutionResult{},
		Vulnerabilities: []Vulnerability{},
	}

	sourcePath, functionName, parseErr := parseTarget(request.Target)
	staticDetails := emptyEscapeDetails()
	staticSummary := ""
	if parseErr == nil {
		staticFindings := runTraditionalStaticEscapeAnalysis(sourcePath, functionName)
		staticDetails = staticFindingsToDetails(sourcePath, staticFindings)
		staticSummary = summarizeStaticFindings(staticFindings)
	}
	staticDetected := len(staticDetails.EscapingReferences) > 0

	// Load target function
	targetFunc, err := loadTargetFunction(request.Target, request.TimeoutSeconds)
	if err != nil {
		errMsg := fmt.Sprintf("Failed to load function: %v", err)
		diagnosis := diagnoseBridgeError(errMsg)
		response.Summary.Crashes = 1
		response.Summary.TotalTests = 0
		response.Summary.Successes = 0
		response.Summary.Timeouts = 0
		response.Summary.Escapes = 0
		response.Summary.GenuineEscapes = 0
		response.Summary.CrashRate = 1.0
		response.Error = errMsg
		response.ErrorCategory = diagnosis.Category
		response.SuggestedAction = diagnosis.SuggestedAction
		return response
	}

	// Run tests
	var successes, crashes, timeouts, escapes, genuineEscapes int
	inputs := request.Inputs
	if len(inputs) == 0 {
		inputs = []string{""}
	}

	for _, input := range inputs {
		for i := 0; i < request.Repeat; i++ {
			result := executeTest(targetFunc, input, request.TimeoutSeconds)
			if staticDetected {
				result.EscapeDetected = true
				result.EscapeDetails = mergeEscapeDetails(result.EscapeDetails, staticDetails)
			}
			response.Results = append(response.Results, result)

			if result.Success {
				successes++
			}
			if result.Crashed {
				crashes++
			}
			if strings.Contains(result.Error, "timeout exceeded") {
				timeouts++
			}
			if result.EscapeDetected {
				escapes++
				if !strings.Contains(result.Error, "timeout exceeded") {
					genuineEscapes++
				}

				// Add vulnerability
				staticCount := len(result.EscapeDetails.EscapingReferences)
				goroutineCount := len(result.EscapeDetails.Goroutines)
				description := fmt.Sprintf("%d goroutine(s) escaped", goroutineCount)
				if staticCount > 0 {
					description = fmt.Sprintf("%d static object escape(s) detected", staticCount)
					if staticSummary != "" {
						description = fmt.Sprintf("%s (%s)", description, staticSummary)
					}
					if goroutineCount > 0 {
						description = fmt.Sprintf("%s + %d goroutine leak(s)", description, goroutineCount)
					}
				}

				vuln := Vulnerability{
					Input:             input,
					VulnerabilityType: "concurrent_escape",
					Severity:          "high",
					Description:       description,
					EscapeDetails:     result.EscapeDetails,
				}
				response.Vulnerabilities = append(response.Vulnerabilities, vuln)
			}
		}
	}

	// Summary
	totalTests := len(response.Results)
	crashRate := 0.0
	if totalTests > 0 {
		crashRate = float64(crashes) / float64(totalTests)
	}
	response.Summary = ExecutionSummary{
		TotalTests:     totalTests,
		Successes:      successes,
		Crashes:        crashes,
		Timeouts:       timeouts,
		Escapes:        escapes,
		GenuineEscapes: genuineEscapes,
		CrashRate:      crashRate,
	}

	return response
}

func loadTargetFunction(target string, timeoutSeconds float64) (func(string) string, error) {
	sourcePath, functionName, err := parseTarget(target)
	if err != nil {
		return nil, err
	}

	binaryPath, tempDir, err := buildTargetRunner(sourcePath, functionName)
	if err != nil {
		return nil, err
	}
	registerTemporaryTargetDir(tempDir)

	timeout := time.Duration(timeoutSeconds * float64(time.Second))
	if timeout <= 0 {
		timeout = 30 * time.Second
	}

	return func(input string) string {
		output, invokeErr := invokeCompiledTarget(binaryPath, timeout, input)
		if invokeErr != nil {
			panic(invokeErr)
		}
		return output
	}, nil
}

func parseTarget(target string) (string, string, error) {
	idx := strings.LastIndex(target, ":")
	if idx <= 0 || idx >= len(target)-1 {
		return "", "", fmt.Errorf("invalid target format '%s': expected 'path/to/file.go:FunctionName'", target)
	}

	filePart := strings.TrimSpace(target[:idx])
	functionName := strings.TrimSpace(target[idx+1:])
	if filePart == "" || functionName == "" {
		return "", "", fmt.Errorf("invalid target format '%s': expected 'path/to/file.go:FunctionName'", target)
	}
	if !isValidGoExportedIdentifier(functionName) {
		return "", "", fmt.Errorf("invalid function name '%s': must be an exported Go identifier", functionName)
	}

	normalized := strings.ReplaceAll(filePart, "\\", string(os.PathSeparator))
	normalized = filepath.Clean(normalized)

	var sourcePath string
	if filepath.IsAbs(normalized) {
		sourcePath = normalized
	} else {
		cwd, err := os.Getwd()
		if err != nil {
			return "", "", fmt.Errorf("failed to resolve current directory: %w", err)
		}
		sourcePath = filepath.Join(cwd, normalized)
	}

	if filepath.Ext(sourcePath) != ".go" {
		return "", "", fmt.Errorf("target file must be a .go file: %s", filePart)
	}

	if _, err := os.Stat(sourcePath); err != nil {
		return "", "", fmt.Errorf("target file does not exist: %s", filePart)
	}

	return sourcePath, functionName, nil
}

func isValidGoExportedIdentifier(name string) bool {
	if name == "" {
		return false
	}

	for i, ch := range name {
		if i == 0 {
			if !(ch >= 'A' && ch <= 'Z') {
				return false
			}
			continue
		}

		if !(ch == '_' || (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9')) {
			return false
		}
	}

	return true
}

func buildTargetRunner(sourcePath string, functionName string) (string, string, error) {
	sourceBytes, err := os.ReadFile(sourcePath)
	if err != nil {
		return "", "", fmt.Errorf("failed to read target file: %w", err)
	}

	rewrittenSource, err := rewriteSourceAsMain(string(sourceBytes))
	if err != nil {
		return "", "", err
	}

	tempDir, err := os.MkdirTemp("", "graphene-go-target-*")
	if err != nil {
		return "", "", fmt.Errorf("failed to create temp directory: %w", err)
	}

	// Avoid the _test.go suffix because `go build` excludes test files.
	targetFile := filepath.Join(tempDir, "target_under_analysis.go")
	if err := os.WriteFile(targetFile, []byte(rewrittenSource), 0644); err != nil {
		_ = os.RemoveAll(tempDir)
		return "", "", fmt.Errorf("failed to write rewritten target file: %w", err)
	}

	entrypointFile := filepath.Join(tempDir, "graphene_entrypoint.go")
	if err := os.WriteFile(entrypointFile, []byte(makeRunnerEntrypoint(functionName)), 0644); err != nil {
		_ = os.RemoveAll(tempDir)
		return "", "", fmt.Errorf("failed to write entrypoint file: %w", err)
	}

	binaryName := "graphene_target_runner"
	if runtime.GOOS == "windows" {
		binaryName += ".exe"
	}
	binaryPath := filepath.Join(tempDir, binaryName)

	cmd := exec.Command("go", "build", "-o", binaryPath, "target_under_analysis.go", "graphene_entrypoint.go")
	cmd.Dir = tempDir
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		_ = os.RemoveAll(tempDir)
		errDetails := strings.TrimSpace(stderr.String())
		if errDetails == "" {
			errDetails = strings.TrimSpace(stdout.String())
		}
		if errDetails == "" {
			errDetails = err.Error()
		}
		return "", "", fmt.Errorf("failed to build target runner: %s", errDetails)
	}

	return binaryPath, tempDir, nil
}

func rewriteSourceAsMain(source string) (string, error) {
	packageRegex := regexp.MustCompile(`(?m)^package\s+[A-Za-z_][A-Za-z0-9_]*`)
	if !packageRegex.MatchString(source) {
		return "", fmt.Errorf("target file is missing a package declaration")
	}

	return packageRegex.ReplaceAllString(source, "package main"), nil
}

func makeRunnerEntrypoint(functionName string) string {
	return fmt.Sprintf(`package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Print(%s(os.Getenv("GRAPHENE_INPUT")))
}
`, functionName)
}

func invokeCompiledTarget(binaryPath string, timeout time.Duration, input string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, binaryPath)
	cmd.Env = append(os.Environ(), "GRAPHENE_INPUT="+input)
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return "", fmt.Errorf("timeout exceeded")
	}
	if err != nil {
		errDetails := strings.TrimSpace(stderr.String())
		if errDetails == "" {
			errDetails = strings.TrimSpace(stdout.String())
		}
		if errDetails == "" {
			errDetails = err.Error()
		}
		return "", fmt.Errorf("target execution failed: %s", errDetails)
	}

	return strings.TrimSpace(stdout.String()), nil
}

func registerTemporaryTargetDir(dir string) {
	temporaryTargetDirs = append(temporaryTargetDirs, dir)
}

func cleanupTemporaryTargets() {
	for _, dir := range temporaryTargetDirs {
		_ = os.RemoveAll(dir)
	}
	temporaryTargetDirs = nil
}

func executeTest(targetFunc func(string) string, input string, timeoutSeconds float64) ExecutionResult {
	result := ExecutionResult{
		InputData:      input,
		Success:        false,
		Crashed:        false,
		EscapeDetected: false,
		EscapeDetails:  emptyEscapeDetails(),
	}

	// Capture baseline goroutine count and stack traces
	baselineStackBuf := make([]byte, 1024*1024)
	baselineStackLen := runtime.Stack(baselineStackBuf, true)
	baselineGoroutineIDs := parseGoroutineIDs(baselineStackBuf[:baselineStackLen])

	startTime := time.Now()
	done := make(chan struct{})
	var output string
	var execErr error

	// Execute function in goroutine with timeout
	go func() {
		defer func() {
			if r := recover(); r != nil {
				switch value := r.(type) {
				case error:
					execErr = value
				default:
					execErr = fmt.Errorf("panic: %v", r)
				}
			}
			close(done)
		}()

		if targetFunc != nil {
			output = targetFunc(input)
		}
	}()

	// Wait with timeout
	timeout := time.Duration(timeoutSeconds * float64(time.Second))
	select {
	case <-done:
		if execErr != nil {
			result.Crashed = true
			result.Error = execErr.Error()
		} else {
			result.Success = true
			result.Output = output
		}
	case <-time.After(timeout):
		result.Crashed = true
		result.Error = "timeout exceeded"
	}

	result.ExecutionTimeMs = time.Since(startTime).Milliseconds()

	// Wait a bit for goroutines to finish
	time.Sleep(100 * time.Millisecond)

	// Check for escaped goroutines with detailed identification
	currentStackBuf := make([]byte, 1024*1024)
	currentStackLen := runtime.Stack(currentStackBuf, true)
	currentGoroutineIDs := parseGoroutineIDs(currentStackBuf[:currentStackLen])

	// Find new goroutines
	escapedGoroutines := make([]GoroutineEscape, 0)
	for gid, info := range currentGoroutineIDs {
		if _, exists := baselineGoroutineIDs[gid]; !exists {
			escapedGoroutines = append(escapedGoroutines, GoroutineEscape{
				GoroutineID: gid,
				State:       info["state"],
				Function:    info["function"],
			})
		}
	}

	if len(escapedGoroutines) > 0 {
		result.EscapeDetected = true
		result.EscapeDetails.Goroutines = escapedGoroutines
	}

	return result
}

func emptyEscapeDetails() EscapeDetails {
	return EscapeDetails{
		EscapingReferences: []ObjectReference{},
		EscapePaths:        []EscapePath{},
		Threads:            []ThreadEscape{},
		Processes:          []ProcessEscape{},
		AsyncTasks:         []AsyncTaskEscape{},
		Goroutines:         []GoroutineEscape{},
		Other:              []string{},
	}
}

func mergeEscapeDetails(primary EscapeDetails, secondary EscapeDetails) EscapeDetails {
	merged := emptyEscapeDetails()
	merged.EscapingReferences = append(merged.EscapingReferences, primary.EscapingReferences...)
	merged.EscapingReferences = append(merged.EscapingReferences, secondary.EscapingReferences...)

	merged.EscapePaths = append(merged.EscapePaths, primary.EscapePaths...)
	merged.EscapePaths = append(merged.EscapePaths, secondary.EscapePaths...)

	merged.Threads = append(merged.Threads, primary.Threads...)
	merged.Threads = append(merged.Threads, secondary.Threads...)

	merged.Processes = append(merged.Processes, primary.Processes...)
	merged.Processes = append(merged.Processes, secondary.Processes...)

	merged.AsyncTasks = append(merged.AsyncTasks, primary.AsyncTasks...)
	merged.AsyncTasks = append(merged.AsyncTasks, secondary.AsyncTasks...)

	merged.Goroutines = append(merged.Goroutines, primary.Goroutines...)
	merged.Goroutines = append(merged.Goroutines, secondary.Goroutines...)

	merged.Other = append(merged.Other, primary.Other...)
	merged.Other = append(merged.Other, secondary.Other...)

	return merged
}

func runTraditionalStaticEscapeAnalysis(sourcePath string, functionName string) []StaticEscapeFinding {
	sourceBytes, err := os.ReadFile(sourcePath)
	if err != nil {
		return []StaticEscapeFinding{}
	}

	lines := strings.Split(string(sourceBytes), "\n")
	packageRetainers := collectPackageRetainers(lines)

	inTarget := false
	braceDepth := 0

	localVars := make(map[string]struct{})
	localObjectVars := make(map[string]struct{})
	objectDependencies := make(map[string]map[string]struct{})

	found := []StaticEscapeFinding{}
	seen := make(map[string]struct{})

	for idx, rawLine := range lines {
		trimmed := strings.TrimSpace(stripGoComment(rawLine))

		if !inTarget {
			if name, ok := extractGoFuncName(trimmed); ok && name == functionName {
				inTarget = true
				braceDepth = strings.Count(trimmed, "{") - strings.Count(trimmed, "}")
				if braceDepth <= 0 {
					braceDepth = 1
				}
			}
			continue
		}

		if name, rhs, ok := extractGoAssignment(trimmed); ok {
			localVars[name] = struct{}{}
			if looksLikeGoObjectInitializer(rhs) {
				localObjectVars[name] = struct{}{}
			}
			for _, id := range extractGoIdentifiers(rhs) {
				if id == name {
					continue
				}
				if _, exists := localVars[id]; exists {
					addGoDependency(objectDependencies, name, id)
					continue
				}
				if _, exists := localObjectVars[id]; exists {
					addGoDependency(objectDependencies, name, id)
				}
			}
		}

		if container, expr, isClosure, ok := extractGoAppendStore(trimmed); ok && isRetainerContainer(container, packageRetainers) {
			escapedVars := resolveGoEscapedVariables(expr, localVars, localObjectVars, objectDependencies)
			for escapedVar := range escapedVars {
				reason := fmt.Sprintf("Local object '%s' stored in retained package container '%s'", escapedVar, container)
				escapeType := "global"
				if isClosure {
					escapeType = "closure"
					reason = fmt.Sprintf("Local object '%s' captured by retained closure in '%s'", escapedVar, container)
				}
				addStaticFinding(
					&found,
					seen,
					StaticEscapeFinding{
						EscapeType:   escapeType,
						Line:         idx + 1,
						Column:       strings.Index(trimmed, container),
						VariableName: escapedVar,
						Reason:       reason,
						Confidence:   "high",
					},
				)
			}
		}

		if container, expr, ok := extractGoIndexAssignment(trimmed); ok {
			if _, localContainer := localObjectVars[container]; localContainer {
				for _, id := range extractGoIdentifiers(expr) {
					if _, exists := localVars[id]; exists {
						addGoDependency(objectDependencies, container, id)
						continue
					}
					if _, exists := localObjectVars[id]; exists {
						addGoDependency(objectDependencies, container, id)
					}
				}
			}

			if isRetainerContainer(container, packageRetainers) {
				escapedVars := resolveGoEscapedVariables(expr, localVars, localObjectVars, objectDependencies)
				for escapedVar := range escapedVars {
					reason := fmt.Sprintf("Local object '%s' assigned into retained package container '%s'", escapedVar, container)
					addStaticFinding(
						&found,
						seen,
						StaticEscapeFinding{
							EscapeType:   "global",
							Line:         idx + 1,
							Column:       strings.Index(trimmed, container),
							VariableName: escapedVar,
							Reason:       reason,
							Confidence:   "high",
						},
					)
				}
			}
		}

		if container, expr, isClosure, ok := extractGoMethodStore(trimmed); ok && isRetainerContainer(container, packageRetainers) {
			escapedVars := resolveGoEscapedVariables(expr, localVars, localObjectVars, objectDependencies)
			for escapedVar := range escapedVars {
				reason := fmt.Sprintf("Local object '%s' stored through retained method on '%s'", escapedVar, container)
				escapeType := "global"
				if isClosure {
					escapeType = "closure"
					reason = fmt.Sprintf("Local object '%s' captured by retained closure stored in '%s'", escapedVar, container)
				}
				addStaticFinding(
					&found,
					seen,
					StaticEscapeFinding{
						EscapeType:   escapeType,
						Line:         idx + 1,
						Column:       strings.Index(trimmed, container),
						VariableName: escapedVar,
						Reason:       reason,
						Confidence:   "high",
					},
				)
			}
		}

		if returned, ok := extractGoReturnIdentifier(trimmed); ok {
			if _, exists := localObjectVars[returned]; exists {
				reason := fmt.Sprintf("Local object '%s' returned from function", returned)
				addStaticFinding(
					&found,
					seen,
					StaticEscapeFinding{
						EscapeType:   "return",
						Line:         idx + 1,
						Column:       strings.Index(trimmed, returned),
						VariableName: returned,
						Reason:       reason,
						Confidence:   "high",
					},
				)
			} else if _, exists := objectDependencies[returned]; exists {
				reason := fmt.Sprintf("Local object '%s' returned from function", returned)
				addStaticFinding(
					&found,
					seen,
					StaticEscapeFinding{
						EscapeType:   "return",
						Line:         idx + 1,
						Column:       strings.Index(trimmed, returned),
						VariableName: returned,
						Reason:       reason,
						Confidence:   "high",
					},
				)
			}
		}

		if strings.Contains(trimmed, "go ") {
			reason := "Goroutine spawned - may not complete before function return"
			addStaticFinding(
				&found,
				seen,
				StaticEscapeFinding{
					EscapeType:   "parameter",
					Line:         idx + 1,
					Column:       strings.Index(trimmed, "go "),
					VariableName: "goroutine",
					Reason:       reason,
					Confidence:   "high",
				},
			)
		}

		braceDepth += strings.Count(trimmed, "{")
		braceDepth -= strings.Count(trimmed, "}")
		if braceDepth <= 0 {
			break
		}
	}

	return found
}

func stripGoComment(line string) string {
	if idx := strings.Index(line, "//"); idx >= 0 {
		return strings.TrimSpace(line[:idx])
	}
	return strings.TrimSpace(line)
}

func addStaticFinding(found *[]StaticEscapeFinding, seen map[string]struct{}, finding StaticEscapeFinding) {
	key := fmt.Sprintf("%s|%d|%s|%s", finding.EscapeType, finding.Line, finding.VariableName, finding.Reason)
	if _, exists := seen[key]; exists {
		return
	}
	seen[key] = struct{}{}
	*found = append(*found, finding)
}

func collectPackageRetainers(lines []string) map[string]struct{} {
	retainers := make(map[string]struct{})
	for _, rawLine := range lines {
		trimmed := stripGoComment(rawLine)
		if !strings.HasPrefix(trimmed, "var ") {
			continue
		}
		name, rhs, ok := extractGoVarAssignment(trimmed)
		if !ok {
			continue
		}
		if isGoRetainerName(name) && looksLikeGoRetainerInitializer(rhs) {
			retainers[name] = struct{}{}
		}
	}
	return retainers
}

func extractGoVarAssignment(line string) (string, string, bool) {
	trimmed := stripGoComment(line)
	if !strings.HasPrefix(trimmed, "var ") {
		return "", "", false
	}
	afterVar := strings.TrimSpace(strings.TrimPrefix(trimmed, "var "))
	assignIdx := strings.Index(afterVar, "=")
	if assignIdx < 0 {
		return "", "", false
	}
	left := strings.TrimSpace(afterVar[:assignIdx])
	if strings.Contains(left, ",") {
		return "", "", false
	}
	name, ok := extractGoLastIdentifier(left)
	if !ok {
		return "", "", false
	}
	rhs := strings.TrimSpace(strings.TrimSuffix(afterVar[assignIdx+1:], ";"))
	if rhs == "" {
		return "", "", false
	}
	return name, rhs, true
}

func extractGoAssignment(line string) (string, string, bool) {
	trimmed := stripGoComment(line)
	if strings.Contains(trimmed, ":=") {
		parts := strings.SplitN(trimmed, ":=", 2)
		left := strings.TrimSpace(parts[0])
		if strings.Contains(left, ",") {
			return "", "", false
		}
		name, ok := extractGoLastIdentifier(left)
		if !ok {
			return "", "", false
		}
		rhs := strings.TrimSpace(strings.TrimSuffix(parts[1], ";"))
		if rhs == "" {
			return "", "", false
		}
		return name, rhs, true
	}

	return extractGoVarAssignment(trimmed)
}

func looksLikeGoRetainerInitializer(rhs string) bool {
	normalized := strings.ToLower(strings.TrimSpace(rhs))
	return strings.HasPrefix(normalized, "[]") ||
		strings.HasPrefix(normalized, "map[") ||
		strings.HasPrefix(normalized, "make([]") ||
		strings.HasPrefix(normalized, "make(map[") ||
		strings.HasPrefix(normalized, "make(chan")
}

func looksLikeGoObjectInitializer(rhs string) bool {
	normalized := strings.ToLower(strings.TrimSpace(rhs))
	return (strings.HasPrefix(normalized, "map[") && strings.Contains(normalized, "{")) ||
		(strings.HasPrefix(normalized, "[]") && strings.Contains(normalized, "{")) ||
		strings.HasPrefix(normalized, "make(map[") ||
		strings.HasPrefix(normalized, "make([]") ||
		strings.HasPrefix(normalized, "make(chan") ||
		(strings.HasPrefix(strings.TrimSpace(rhs), "&") && strings.Contains(rhs, "{"))
}

func isGoRetainerName(name string) bool {
	lower := strings.ToLower(name)
	for _, hint := range goRetainerHints {
		if strings.Contains(lower, hint) {
			return true
		}
	}
	return false
}

func isRetainerContainer(name string, retainers map[string]struct{}) bool {
	if _, exists := retainers[name]; exists {
		return true
	}
	return isGoRetainerName(name)
}

func extractGoIdentifiers(text string) []string {
	matches := goIdentifierRegex.FindAllString(text, -1)
	ids := make([]string, 0, len(matches))
	for _, token := range matches {
		if _, isKeyword := goKeywords[token]; isKeyword {
			continue
		}
		ids = append(ids, token)
	}
	return ids
}

func extractGoLastIdentifier(text string) (string, bool) {
	ids := extractGoIdentifiers(text)
	if len(ids) == 0 {
		return "", false
	}
	return ids[len(ids)-1], true
}

func addGoDependency(deps map[string]map[string]struct{}, variable string, dependency string) {
	if _, exists := deps[variable]; !exists {
		deps[variable] = make(map[string]struct{})
	}
	deps[variable][dependency] = struct{}{}
}

func resolveGoEscapedVariables(
	expression string,
	localVars map[string]struct{},
	localObjectVars map[string]struct{},
	dependencies map[string]map[string]struct{},
) map[string]struct{} {
	escaped := make(map[string]struct{})
	for _, identifier := range extractGoIdentifiers(expression) {
		if _, exists := localVars[identifier]; exists {
			escaped[identifier] = struct{}{}
			expandGoDependencies(identifier, dependencies, escaped, map[string]struct{}{})
			continue
		}
		if _, exists := localObjectVars[identifier]; exists {
			escaped[identifier] = struct{}{}
			expandGoDependencies(identifier, dependencies, escaped, map[string]struct{}{})
		}
	}
	return escaped
}

func expandGoDependencies(
	variable string,
	dependencies map[string]map[string]struct{},
	output map[string]struct{},
	visited map[string]struct{},
) {
	if _, seen := visited[variable]; seen {
		return
	}
	visited[variable] = struct{}{}

	nextDeps, exists := dependencies[variable]
	if !exists {
		return
	}

	for dep := range nextDeps {
		output[dep] = struct{}{}
		expandGoDependencies(dep, dependencies, output, visited)
	}
}

func extractGoAppendStore(line string) (string, string, bool, bool) {
	trimmed := strings.TrimSpace(strings.TrimSuffix(stripGoComment(line), ";"))
	assignIdx := strings.Index(trimmed, "=")
	if assignIdx < 0 {
		return "", "", false, false
	}

	lhs := strings.TrimSpace(trimmed[:assignIdx])
	container, ok := extractGoLastIdentifier(lhs)
	if !ok {
		return "", "", false, false
	}

	rhs := strings.TrimSpace(trimmed[assignIdx+1:])
	if !strings.HasPrefix(rhs, "append(") || !strings.HasSuffix(rhs, ")") {
		return "", "", false, false
	}

	inside := rhs[len("append(") : len(rhs)-1]
	_, valueExpr, split := splitGoTopLevelComma(inside)
	if !split {
		return "", "", false, false
	}
	valueExpr = strings.TrimSpace(valueExpr)
	return container, valueExpr, strings.Contains(valueExpr, "func("), true
}

func extractGoIndexAssignment(line string) (string, string, bool) {
	trimmed := strings.TrimSpace(strings.TrimSuffix(stripGoComment(line), ";"))
	if strings.Contains(trimmed, "==") {
		return "", "", false
	}
	assignIdx := strings.Index(trimmed, "=")
	if assignIdx < 0 {
		return "", "", false
	}
	left := strings.TrimSpace(trimmed[:assignIdx])
	bracketIdx := strings.Index(left, "[")
	if bracketIdx < 0 {
		return "", "", false
	}
	container, ok := extractGoLastIdentifier(left[:bracketIdx])
	if !ok {
		return "", "", false
	}
	rhs := strings.TrimSpace(trimmed[assignIdx+1:])
	if rhs == "" {
		return "", "", false
	}
	return container, rhs, true
}

func extractGoMethodStore(line string) (string, string, bool, bool) {
	trimmed := strings.TrimSpace(strings.TrimSuffix(stripGoComment(line), ";"))
	dotIdx := strings.Index(trimmed, ".")
	openIdx := strings.Index(trimmed, "(")
	closeIdx := strings.LastIndex(trimmed, ")")
	if dotIdx < 0 || openIdx < 0 || closeIdx < 0 || dotIdx > openIdx {
		return "", "", false, false
	}

	receiver, ok := extractGoLastIdentifier(trimmed[:dotIdx])
	if !ok {
		return "", "", false, false
	}

	method := strings.TrimSpace(trimmed[dotIdx+1 : openIdx])
	if method != "Store" && method != "Set" && method != "Add" && method != "Push" && method != "Insert" {
		return "", "", false, false
	}

	inside := strings.TrimSpace(trimmed[openIdx+1 : closeIdx])
	if inside == "" {
		return "", "", false, false
	}

	valueExpr := inside
	if method == "Store" || method == "Set" || method == "Insert" {
		_, rhs, split := splitGoTopLevelComma(inside)
		if split {
			valueExpr = strings.TrimSpace(rhs)
		}
	}

	return receiver, valueExpr, strings.Contains(valueExpr, "func("), true
}

func splitGoTopLevelComma(text string) (string, string, bool) {
	parenDepth := 0
	braceDepth := 0
	bracketDepth := 0

	for idx, ch := range text {
		switch ch {
		case '(':
			parenDepth++
		case ')':
			parenDepth--
		case '{':
			braceDepth++
		case '}':
			braceDepth--
		case '[':
			bracketDepth++
		case ']':
			bracketDepth--
		case ',':
			if parenDepth == 0 && braceDepth == 0 && bracketDepth == 0 {
				left := text[:idx]
				right := text[idx+1:]
				return left, right, true
			}
		}
	}

	return "", "", false
}

func extractGoReturnIdentifier(line string) (string, bool) {
	trimmed := strings.TrimSpace(strings.TrimSuffix(stripGoComment(line), ";"))
	matches := goReturnIdentifierRegex.FindStringSubmatch(trimmed)
	if len(matches) != 2 {
		return "", false
	}
	return matches[1], true
}

func extractGoFuncName(line string) (string, bool) {
	if !strings.Contains(line, "func ") {
		return "", false
	}
	funcIdx := strings.Index(line, "func ")
	after := strings.TrimSpace(line[funcIdx+len("func "):])
	if strings.HasPrefix(after, "(") {
		receiverEnd := strings.Index(after, ")")
		if receiverEnd < 0 {
			return "", false
		}
		after = strings.TrimSpace(after[receiverEnd+1:])
	}

	name := ""
	for _, ch := range after {
		if (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') || ch == '_' {
			name += string(ch)
			continue
		}
		break
	}

	if name == "" {
		return "", false
	}
	return name, true
}

func staticFindingsToDetails(sourcePath string, findings []StaticEscapeFinding) EscapeDetails {
	details := emptyEscapeDetails()

	for _, finding := range findings {
		details.EscapingReferences = append(details.EscapingReferences, ObjectReference{
			VariableName:   finding.VariableName,
			ObjectType:     "unknown",
			AllocationSite: fmt.Sprintf("%s:%d:%d", sourcePath, finding.Line, finding.Column),
			EscapedVia:     finding.EscapeType,
		})

		details.EscapePaths = append(details.EscapePaths, EscapePath{
			Source:      finding.VariableName,
			Destination: staticDestination(finding.EscapeType),
			EscapeType:  finding.EscapeType,
			Confidence:  finding.Confidence,
		})
	}

	return details
}

func summarizeStaticFindings(findings []StaticEscapeFinding) string {
	if len(findings) == 0 {
		return ""
	}

	parts := make([]string, 0, len(findings))
	for _, finding := range findings {
		parts = append(parts, fmt.Sprintf("%s:%s@L%d", finding.EscapeType, finding.VariableName, finding.Line))
	}

	return strings.Join(parts, "; ")
}

func staticDestination(escapeType string) string {
	switch escapeType {
	case "return":
		return "caller"
	case "parameter":
		return "callee"
	case "global":
		return "module_scope"
	case "closure":
		return "closure_scope"
	default:
		return "heap_container"
	}
}

// parseGoroutineIDs extracts goroutine IDs and function names from stack traces
func parseGoroutineIDs(stackData []byte) map[uint64]map[string]string {
	goroutines := make(map[uint64]map[string]string)

	lines := bytes.Split(stackData, []byte("\n"))
	goroutineIDRegex := regexp.MustCompile(`goroutine (\d+) \[(.+?)\]`)

	for i := 0; i < len(lines); i++ {
		line := string(lines[i])
		if matches := goroutineIDRegex.FindStringSubmatch(line); matches != nil {
			gid, _ := strconv.ParseUint(matches[1], 10, 64)
			state := matches[2]

			// Extract function from next line
			function := "unknown"
			if i+1 < len(lines) {
				nextLine := string(lines[i+1])
				if parts := strings.Fields(nextLine); len(parts) > 0 {
					function = strings.TrimSpace(parts[0])
				}
			}

			goroutines[gid] = map[string]string{
				"state":    state,
				"function": function,
			}
		}
	}

	return goroutines
}

func errorResponse(message string) {
	diagnosis := diagnoseBridgeError(message)
	response := AnalyzeResponse{
		SessionID:       "unknown",
		Language:        "go",
		AnalyzerVersion: "1.0.0",
		Results:         []ExecutionResult{},
		Vulnerabilities: []Vulnerability{},
		Summary: ExecutionSummary{
			Crashes:   1,
			CrashRate: 1.0,
		},
		Error:           message,
		ErrorCategory:   diagnosis.Category,
		SuggestedAction: diagnosis.SuggestedAction,
	}

	responseBytes, _ := json.MarshalIndent(response, "", "  ")
	fmt.Fprintln(os.Stderr, string(responseBytes))
	os.Exit(1)
}

func diagnoseBridgeError(message string) ErrorDiagnosis {
	lower := strings.ToLower(strings.TrimSpace(message))

	if strings.Contains(lower, "timeout") || strings.Contains(lower, "timed out") || strings.Contains(lower, "exceeded") {
		return ErrorDiagnosis{
			Category:        "Timeout",
			SuggestedAction: "Inspect blocking operations and missing joins/awaits before increasing timeout.",
		}
	}

	if strings.Contains(lower, "target resolution") ||
		strings.Contains(lower, "missing required field: 'target'") ||
		strings.Contains(lower, "target loading failed") ||
		strings.Contains(lower, "failed to load") ||
		strings.Contains(lower, "invalid target") ||
		strings.Contains(lower, "module not found") ||
		(strings.Contains(lower, "function") && strings.Contains(lower, "not found")) {
		return ErrorDiagnosis{
			Category:        "Target Resolution",
			SuggestedAction: "Verify target signature/path and ensure the target symbol exists in the selected language module.",
		}
	}

	if strings.Contains(lower, "protocol/input") ||
		strings.Contains(lower, "invalid json") ||
		strings.Contains(lower, "failed to parse") ||
		strings.Contains(lower, "empty input") ||
		strings.Contains(lower, "expected json") ||
		strings.Contains(lower, "json") ||
		strings.Contains(lower, "parse") ||
		strings.Contains(lower, "stdin") ||
		strings.Contains(lower, "protocol") {
		return ErrorDiagnosis{
			Category:        "Protocol/Input",
			SuggestedAction: "Validate request JSON and ensure bridge stdin/stdout protocol fields match the orchestrator contract.",
		}
	}

	if strings.Contains(lower, "environment") ||
		strings.Contains(lower, "permission denied") ||
		strings.Contains(lower, "not available") ||
		strings.Contains(lower, "not found in path") ||
		strings.Contains(lower, "command not found") ||
		strings.Contains(lower, "missing tools") ||
		strings.Contains(lower, "go not found") {
		return ErrorDiagnosis{
			Category:        "Environment",
			SuggestedAction: "Check runtime/toolchain installation and PATH configuration for the selected language analyzer.",
		}
	}

	if strings.Contains(lower, "runtime crash") ||
		strings.Contains(lower, "panic") ||
		strings.Contains(lower, "exception") ||
		strings.Contains(lower, "traceback") ||
		strings.Contains(lower, "segmentation") {
		return ErrorDiagnosis{
			Category:        "Runtime Crash",
			SuggestedAction: "Re-run with --verbose and inspect bridge stack traces for runtime exceptions.",
		}
	}

	return ErrorDiagnosis{
		Category:        "Unknown",
		SuggestedAction: "Re-run with --verbose and inspect bridge stdout/stderr for additional diagnostics.",
	}
}
