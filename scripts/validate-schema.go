// Validate skewer.yaml files against the JSON Schema using Go
//
// Build:
//   go build -o validate-schema scripts/validate-schema.go
//
// Usage:
//   ./validate-schema skewer.yaml
//   ./validate-schema examples/*.yaml
//
// Dependencies:
//   go get github.com/xeipuuv/gojsonschema
//   go get gopkg.in/yaml.v3

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/xeipuuv/gojsonschema"
	"gopkg.in/yaml.v3"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: validate-schema <yaml-file> [yaml-file ...]")
		fmt.Fprintln(os.Stderr, "")
		fmt.Fprintln(os.Stderr, "Example:")
		fmt.Fprintln(os.Stderr, "  ./validate-schema skewer.yaml")
		fmt.Fprintln(os.Stderr, "  ./validate-schema examples/*.yaml")
		os.Exit(1)
	}

	// Load schema
	exePath, err := os.Executable()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting executable path: %v\n", err)
		os.Exit(1)
	}

	scriptDir := filepath.Dir(exePath)
	schemaPath := filepath.Join(scriptDir, "..", "skewer-schema.json")

	// Try current directory if not found
	if _, err := os.Stat(schemaPath); os.IsNotExist(err) {
		schemaPath = "skewer-schema.json"
	}

	schemaLoader := gojsonschema.NewReferenceLoader("file://" + schemaPath)

	// Validate each file
	results := []result{}
	maxPathLen := 0

	for _, yamlPath := range os.Args[1:] {
		if len(yamlPath) > maxPathLen {
			maxPathLen = len(yamlPath)
		}

		success, message := validateFile(yamlPath, schemaLoader)
		results = append(results, result{
			path:    yamlPath,
			success: success,
			message: message,
		})
	}

	// Print results
	for _, r := range results {
		pathStr := fmt.Sprintf("%-*s", maxPathLen, r.path)
		fmt.Printf("%s  %s\n", pathStr, r.message)
	}

	// Exit with error if any validation failed
	failed := false
	for _, r := range results {
		if !r.success {
			failed = true
			break
		}
	}

	if failed {
		os.Exit(1)
	}

	fmt.Printf("\n✓ All %d file(s) valid\n", len(results))
	os.Exit(0)
}

type result struct {
	path    string
	success bool
	message string
}

func validateFile(yamlPath string, schemaLoader gojsonschema.JSONLoader) (bool, string) {
	// Check file exists
	if _, err := os.Stat(yamlPath); os.IsNotExist(err) {
		return false, fmt.Sprintf("✗ File not found: %s", yamlPath)
	}

	// Load YAML file
	data, err := os.ReadFile(yamlPath)
	if err != nil {
		return false, fmt.Sprintf("✗ Error reading file: %v", err)
	}

	// Parse YAML
	var yamlData interface{}
	if err := yaml.Unmarshal(data, &yamlData); err != nil {
		return false, fmt.Sprintf("✗ YAML parsing error: %v", err)
	}

	// Convert to JSON (required for gojsonschema)
	jsonData, err := json.Marshal(yamlData)
	if err != nil {
		return false, fmt.Sprintf("✗ Error converting to JSON: %v", err)
	}

	// Validate against schema
	documentLoader := gojsonschema.NewBytesLoader(jsonData)
	result, err := gojsonschema.Validate(schemaLoader, documentLoader)
	if err != nil {
		return false, fmt.Sprintf("✗ Validation error: %v", err)
	}

	if !result.Valid() {
		// Format the first error nicely
		if len(result.Errors()) > 0 {
			err := result.Errors()[0]
			path := err.Field()
			if path == "(root)" {
				path = "root"
			}
			return false, fmt.Sprintf("✗ Validation error at %s: %s", path, err.Description())
		}
		return false, "✗ Validation failed"
	}

	return true, "✓ Valid"
}

func formatPath(path string) string {
	// Convert "(root).sites.west.platform" to "sites → west → platform"
	path = strings.TrimPrefix(path, "(root)")
	path = strings.TrimPrefix(path, ".")
	parts := strings.Split(path, ".")
	return strings.Join(parts, " → ")
}
