package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"strings"
)

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

// GoStaticAnalyzer performs static analysis on Go source code
type GoStaticAnalyzer struct {
	sourceFile   string
	functionName string
	fset         *token.FileSet
	sourceLines  []string
	escapes      []StaticEscape
	inFunction   bool
	channels     map[string]bool // track channel variables
	received     map[string]bool // track channels that have been received on
}

func newGoStaticAnalyzer(sourceFile, functionName string) *GoStaticAnalyzer {
	return &GoStaticAnalyzer{
		sourceFile:   sourceFile,
		functionName: functionName,
		fset:         token.NewFileSet(),
		channels:     make(map[string]bool),
		received:     make(map[string]bool),
	}
}

func (gsa *GoStaticAnalyzer) analyze() error {
	// Read source file
	content, err := os.ReadFile(gsa.sourceFile)
	if err != nil {
		return fmt.Errorf("failed to read source file: %w", err)
	}
	gsa.sourceLines = strings.Split(string(content), "\n")

	// Parse the Go source file
	node, err := parser.ParseFile(gsa.fset, gsa.sourceFile, nil, parser.ParseComments)
	if err != nil {
		return fmt.Errorf("failed to parse source file: %w", err)
	}

	// Walk the AST
	ast.Inspect(node, gsa.visit)

	// Check for unjoined channels at the end
	gsa.checkUnreceivedChannels()

	return nil
}

func (gsa *GoStaticAnalyzer) visit(n ast.Node) bool {
	switch node := n.(type) {
	case *ast.FuncDecl:
		// Check if this is our target function
		if node.Name.Name == gsa.functionName {
			gsa.inFunction = true
			// Process function body
			if node.Body != nil {
				ast.Inspect(node.Body, gsa.visitBody)
			}
			gsa.inFunction = false
			return false // Don't descend further
		}
	}
	return true
}

func (gsa *GoStaticAnalyzer) visitBody(n ast.Node) bool {
	if !gsa.inFunction {
		return true
	}

	switch node := n.(type) {
	case *ast.GoStmt:
		// Goroutine spawn detected
		pos := gsa.fset.Position(node.Pos())
		snippet := gsa.getCodeSnippet(pos.Line)
		gsa.escapes = append(gsa.escapes, StaticEscape{
			EscapeType:   "concurrency",
			Line:         pos.Line,
			Column:       pos.Column,
			VariableName: "goroutine",
			Reason:       "Goroutine spawned - may not complete before function return",
			Confidence:   "high",
			CodeSnippet:  &snippet,
		})

	case *ast.AssignStmt:
		// Check for channel creation: ch := make(chan ...)
		for i, rhs := range node.Rhs {
			if call, ok := rhs.(*ast.CallExpr); ok {
				if ident, ok := call.Fun.(*ast.Ident); ok && ident.Name == "make" {
					if len(call.Args) > 0 {
						if chanType, ok := call.Args[0].(*ast.ChanType); ok {
							// This is a channel creation
							if i < len(node.Lhs) {
								if lhsIdent, ok := node.Lhs[i].(*ast.Ident); ok {
									gsa.channels[lhsIdent.Name] = true
								}
							}
						}
					}
				}
			}
		}

	case *ast.UnaryExpr:
		// Check for channel receive: <-ch
		if node.Op == token.ARROW {
			if ident, ok := node.X.(*ast.Ident); ok {
				gsa.received[ident.Name] = true
			}
		}

	case *ast.SendStmt:
		// Channel send doesn't mark as received, but it's a use
		// We mainly care about blocking receives
	}

	return true
}

func (gsa *GoStaticAnalyzer) checkUnreceivedChannels() {
	for chanName := range gsa.channels {
		if !gsa.received[chanName] {
			// Channel created but never received on - potential goroutine leak
			gsa.escapes = append(gsa.escapes, StaticEscape{
				EscapeType:   "concurrency",
				Line:         0, // We'd need to track the line where it was created
				Column:       0,
				VariableName: chanName,
				Reason:       fmt.Sprintf("Channel '%s' created but never received on (goroutine may leak)", chanName),
				Confidence:   "medium",
			})
		}
	}
}

func (gsa *GoStaticAnalyzer) getCodeSnippet(line int) string {
	if line > 0 && line <= len(gsa.sourceLines) {
		return strings.TrimSpace(gsa.sourceLines[line-1])
	}
	return ""
}

func main() {
	if len(os.Args) != 3 {
		result := StaticAnalysisResult{
			Success: false,
			Escapes: []StaticEscape{},
		}
		errMsg := "Usage: static_analyzer <source_file> <function_name>"
		result.Error = &errMsg
		json.NewEncoder(os.Stdout).Encode(result)
		os.Exit(1)
	}

	sourceFile := os.Args[1]
	functionName := os.Args[2]

	analyzer := newGoStaticAnalyzer(sourceFile, functionName)
	err := analyzer.analyze()

	result := StaticAnalysisResult{
		Escapes: analyzer.escapes,
		Success: err == nil,
	}

	if err != nil {
		errMsg := err.Error()
		result.Error = &errMsg
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	encoder.Encode(result)
}
