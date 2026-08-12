package logger

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/skupperproject/sketcher/internal/utils"
)

// RunLogger logs execution details for demo and test runs
type RunLogger struct {
	logFile    *os.File
	logPath    string
	startTime  time.Time
	stepCount  int
	runType    string // "demo" or "test"
	yamlFile   string
	workDir    string
}

// LogEntry represents a single log entry
type LogEntry struct {
	Timestamp   string                 `json:"timestamp"`
	Type        string                 `json:"type"` // "step", "command", "wait", "error", "info"
	StepNumber  int                    `json:"step_number,omitempty"`
	StepName    string                 `json:"step_name,omitempty"`
	Site        string                 `json:"site,omitempty"`
	Command     string                 `json:"command,omitempty"`
	WaitType    string                 `json:"wait_type,omitempty"`
	WaitTarget  string                 `json:"wait_target,omitempty"`
	WaitTimeout int                    `json:"wait_timeout,omitempty"`
	Message     string                 `json:"message,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Duration    float64                `json:"duration,omitempty"`
	Context     map[string]interface{} `json:"context,omitempty"`
}

// New creates a new RunLogger
func New(runType, yamlFile, workDir string) (*RunLogger, error) {
	if workDir == "" {
		workDir = "/tmp/sketcher"
	}

	if err := os.MkdirAll(workDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create work directory: %w", err)
	}

	timestamp := time.Now().Format("20060102-150405")
	logFileName := fmt.Sprintf("sketcher-%s-%s.log", runType, timestamp)
	logPath := filepath.Join(workDir, logFileName)

	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to create log file: %w", err)
	}

	logger := &RunLogger{
		logFile:   logFile,
		logPath:   logPath,
		startTime: time.Now(),
		runType:   runType,
		yamlFile:  yamlFile,
		workDir:   workDir,
	}

	// Log run start
	logger.LogInfo("Run started", map[string]interface{}{
		"run_type":  runType,
		"yaml_file": yamlFile,
		"work_dir":  workDir,
	})

	return logger, nil
}

// LogStep logs the start of a step
func (l *RunLogger) LogStep(stepNumber int, stepName string) {
	l.stepCount++
	entry := LogEntry{
		Timestamp:  time.Now().Format(time.RFC3339),
		Type:       "step",
		StepNumber: stepNumber,
		StepName:   stepName,
	}
	l.writeEntry(entry)
}

// LogCommand logs a command execution
func (l *RunLogger) LogCommand(site, command string, background bool) {
	context := map[string]interface{}{
		"background": background,
	}
	entry := LogEntry{
		Timestamp: time.Now().Format(time.RFC3339),
		Type:      "command",
		Site:      site,
		Command:   command,
		Context:   context,
	}
	l.writeEntry(entry)
}

// LogWait logs a wait operation
func (l *RunLogger) LogWait(waitType, target string, timeout int, site string) {
	entry := LogEntry{
		Timestamp:   time.Now().Format(time.RFC3339),
		Type:        "wait",
		WaitType:    waitType,
		WaitTarget:  target,
		WaitTimeout: timeout,
		Site:        site,
	}
	l.writeEntry(entry)
}

// LogError logs an error
func (l *RunLogger) LogError(err error, context map[string]interface{}) {
	entry := LogEntry{
		Timestamp: time.Now().Format(time.RFC3339),
		Type:      "error",
		Error:     err.Error(),
		Context:   context,
	}
	l.writeEntry(entry)
}

// LogInfo logs general information
func (l *RunLogger) LogInfo(message string, context map[string]interface{}) {
	entry := LogEntry{
		Timestamp: time.Now().Format(time.RFC3339),
		Type:      "info",
		Message:   message,
		Context:   context,
	}
	l.writeEntry(entry)
}

// LogStepComplete logs step completion with duration
func (l *RunLogger) LogStepComplete(stepNumber int, stepName string, duration time.Duration) {
	entry := LogEntry{
		Timestamp:  time.Now().Format(time.RFC3339),
		Type:       "step_complete",
		StepNumber: stepNumber,
		StepName:   stepName,
		Duration:   duration.Seconds(),
	}
	l.writeEntry(entry)
}

// Close closes the log file and logs run summary
func (l *RunLogger) Close() error {
	if l.logFile == nil {
		return nil
	}

	totalDuration := time.Since(l.startTime)
	l.LogInfo("Run completed", map[string]interface{}{
		"total_duration_seconds": totalDuration.Seconds(),
		"total_steps":            l.stepCount,
	})

	utils.Info("Log file: %s", l.logPath)

	return l.logFile.Close()
}

// writeEntry writes a log entry as JSON
func (l *RunLogger) writeEntry(entry LogEntry) {
	if l.logFile == nil {
		return
	}

	data, err := json.Marshal(entry)
	if err != nil {
		utils.Warn("Failed to marshal log entry: %v", err)
		return
	}

	if _, err := l.logFile.Write(append(data, '\n')); err != nil {
		utils.Warn("Failed to write log entry: %v", err)
	}
}

// GetLogPath returns the path to the log file
func (l *RunLogger) GetLogPath() string {
	return l.logPath
}
