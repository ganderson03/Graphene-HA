package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
)

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
	Threads    []ThreadEscape    `json:"threads"`
	Processes  []ProcessEscape   `json:"processes"`
	AsyncTasks []AsyncTaskEscape `json:"async_tasks"`
	Goroutines []GoroutineEscape `json:"goroutines"`
	Other      []string          `json:"other"`
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

	// Load target function
	targetFunc, err := loadTargetFunction(request.Target)
	if err != nil {
		response.Summary.Crashes = 1
		response.Summary.CrashRate = 1.0
		response.Error = fmt.Sprintf("Failed to load function: %v", err)
		return response
	}

	// Run tests
	var successes, crashes, timeouts, escapes, genuineEscapes int

	for _, input := range request.Inputs {
		for i := 0; i < request.Repeat; i++ {
			result := executeTest(targetFunc, input, request.TimeoutSeconds)
			response.Results = append(response.Results, result)

			if result.Success {
				successes++
			}
			if result.Crashed {
				crashes++
			}
			if result.Error == "timeout exceeded" {
				timeouts++
			}
			if result.EscapeDetected {
				escapes++
				if result.Error != "timeout exceeded" {
					genuineEscapes++
				}

				// Add vulnerability
				vuln := Vulnerability{
					Input:             input,
					VulnerabilityType: "concurrent_escape",
					Severity:          "high",
					Description:       fmt.Sprintf("%d goroutine(s) escaped", len(result.EscapeDetails.Goroutines)),
					EscapeDetails:     result.EscapeDetails,
				}
				response.Vulnerabilities = append(response.Vulnerabilities, vuln)
			}
		}
	}

	// Summary
	totalTests := len(response.Results)
	response.Summary = ExecutionSummary{
		TotalTests:     totalTests,
		Successes:      successes,
		Crashes:        crashes,
		Timeouts:       timeouts,
		Escapes:        escapes,
		GenuineEscapes: genuineEscapes,
		CrashRate:      float64(crashes) / float64(totalTests),
	}

	return response
}

func loadTargetFunction(_ string) (func(string) string, error) {
	// For Go, we need to load a plugin
	// Format: file.so:FunctionName
	// Note: Go plugins only work on Linux/macOS

	// This is a simplified version - actual implementation would need plugin loading
	return nil, fmt.Errorf("Go plugin loading not yet implemented")
}

func executeTest(targetFunc func(string) string, input string, timeoutSeconds float64) ExecutionResult {
	result := ExecutionResult{
		InputData:      input,
		Success:        false,
		Crashed:        false,
		EscapeDetected: false,
		EscapeDetails: EscapeDetails{
			Threads:    []ThreadEscape{},
			Processes:  []ProcessEscape{},
			AsyncTasks: []AsyncTaskEscape{},
			Goroutines: []GoroutineEscape{},
			Other:      []string{},
		},
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
				execErr = fmt.Errorf("panic: %v", r)
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
		Error: message,
	}

	responseBytes, _ := json.MarshalIndent(response, "", "  ")
	fmt.Fprintln(os.Stderr, string(responseBytes))
	os.Exit(1)
}
