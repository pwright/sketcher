package logger

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// ViewLog displays a log file in a human-readable format
func ViewLog(logPath string) error {
	file, err := os.Open(logPath)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := scanner.Text()

		var entry LogEntry
		if err := json.Unmarshal([]byte(line), &entry); err != nil {
			fmt.Printf("Line %d: Failed to parse: %v\n", lineNum, err)
			continue
		}

		formatLogEntry(&entry)
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error reading log file: %w", err)
	}

	return nil
}

// formatLogEntry formats a single log entry for display
func formatLogEntry(entry *LogEntry) {
	timestamp := entry.Timestamp
	if len(timestamp) > 19 {
		timestamp = timestamp[11:19] // Extract time portion
	}

	switch entry.Type {
	case "info":
		fmt.Printf("[%s] INFO: %s\n", timestamp, entry.Message)
		if entry.Context != nil {
			printContext(entry.Context, "  ")
		}

	case "step":
		stepLabel := fmt.Sprintf("STEP %d: %s", entry.StepNumber, entry.StepName)
		fmt.Printf("\n[%s] %s\n", timestamp, stepLabel)
		fmt.Println(strings.Repeat("─", len(stepLabel)+len(timestamp)+4))

	case "step_complete":
		fmt.Printf("[%s] ✓ Step %d completed in %.2fs\n", timestamp, entry.StepNumber, entry.Duration)

	case "command":
		bg := ""
		if ctx, ok := entry.Context["background"].(bool); ok && ctx {
			bg = " (background)"
		}
		fmt.Printf("[%s] CMD [%s]%s: %s\n", timestamp, entry.Site, bg, entry.Command)

	case "wait":
		fmt.Printf("[%s] WAIT [%s]: %s for %s (timeout: %ds)\n",
			timestamp, entry.Site, entry.WaitType, entry.WaitTarget, entry.WaitTimeout)

	case "error":
		fmt.Printf("[%s] ERROR: %s\n", timestamp, entry.Error)
		if entry.Context != nil {
			printContext(entry.Context, "  ")
		}

	default:
		fmt.Printf("[%s] %s: %+v\n", timestamp, entry.Type, entry)
	}
}

// printContext prints context data with indentation
func printContext(context map[string]interface{}, indent string) {
	for k, v := range context {
		fmt.Printf("%s%s: %v\n", indent, k, v)
	}
}
