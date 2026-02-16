package main

// StaticAnalysis result structures
type StaticEscape struct {
	EscapeType   string  `json:"escape_type"`
	Line         int     `json:"line"`
	Column       int     `json:"column"`
	VariableName string  `json:"variable_name"`
	Reason       string  `json:"reason"`
	Confidence   string  `json:"confidence"`
	CodeSnippet  *string `json:"code_snippet,omitempty"`
}

type StaticAnalysisResult struct {
	Escapes []StaticEscape `json:"escapes"`
	Success bool           `json:"success"`
	Error   *string        `json:"error,omitempty"`
}


