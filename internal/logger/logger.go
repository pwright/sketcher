package logger

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
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
	execMode   string // "kind", "minikube", "native", etc.
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
func New(runType, yamlFile, workDir, execMode, version string) (*RunLogger, error) {
	// Always write logs to /tmp/sk-logs/ to prevent deletion during cleanup
	logDir := "/tmp/sk-logs"

	if err := os.MkdirAll(logDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create log directory: %w", err)
	}

	// Extract base filename from YAML path (without extension)
	yamlBase := filepath.Base(yamlFile)
	yamlBase = strings.TrimSuffix(yamlBase, filepath.Ext(yamlBase))

	timestamp := time.Now().Format("20060102-150405")
	logFileName := fmt.Sprintf("%s-%s.log", yamlBase, timestamp)
	logPath := filepath.Join(logDir, logFileName)

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
		execMode:  execMode,
	}

	// Log environment info as first entry
	logger.logEnvironment(version)

	// Log execution context as second entry
	execContext := map[string]interface{}{
		"run_type":  runType,
		"yaml_file": yamlFile,
		"work_dir":  workDir,
		"log_dir":   logDir,
		"log_file":  logPath,
	}
	if execMode != "" {
		execContext["exec_mode"] = execMode
	}
	logger.LogInfo("Execution context", execContext)

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

// logEnvironment logs system environment information
func (l *RunLogger) logEnvironment(version string) {
	env := make(map[string]interface{})

	// Sketcher version
	if version != "" {
		env["sketcher_version"] = version
	}

	// Basic system info
	env["os"] = runtime.GOOS
	env["arch"] = runtime.GOARCH
	env["go_version"] = runtime.Version()
	env["num_cpu"] = runtime.NumCPU()

	// Hostname
	if hostname, err := os.Hostname(); err == nil {
		env["hostname"] = hostname
	}

	// Current user
	if user := os.Getenv("USER"); user != "" {
		env["user"] = user
	}

	// Home directory
	if home, err := os.UserHomeDir(); err == nil {
		env["home_dir"] = home
	}

	// Current working directory
	if cwd, err := os.Getwd(); err == nil {
		env["cwd"] = cwd
	}

	// Kubernetes config location
	kubeconfig := os.Getenv("KUBECONFIG")
	if kubeconfig == "" {
		if home, err := os.UserHomeDir(); err == nil {
			kubeconfig = filepath.Join(home, ".kube", "config")
		}
	}
	if kubeconfig != "" {
		env["kubeconfig_path"] = kubeconfig
	}

	// Kubernetes context (if available)
	if output, err := exec.Command("kubectl", "config", "current-context").Output(); err == nil {
		env["k8s_context"] = strings.TrimSpace(string(output))
	}

	// Check for minikube
	if output, err := exec.Command("minikube", "status", "-f", "{{.Host}}").Output(); err == nil {
		env["minikube_status"] = strings.TrimSpace(string(output))
		// Get minikube profile
		if profile, err := exec.Command("minikube", "profile").Output(); err == nil {
			env["minikube_profile"] = strings.TrimSpace(string(profile))
		}
	}

	// Check for kind clusters
	if output, err := exec.Command("kind", "get", "clusters").Output(); err == nil {
		clusters := strings.Split(strings.TrimSpace(string(output)), "\n")
		if len(clusters) > 0 && clusters[0] != "" {
			env["kind_clusters"] = clusters
		}
	}

	// Skupper version and location (if available)
	if skupperPath, err := exec.LookPath("skupper"); err == nil {
		env["skupper_path"] = skupperPath
		if output, err := exec.Command("skupper", "version").Output(); err == nil {
			env["skupper_version"] = strings.TrimSpace(string(output))
		}
	}

	// Kubectl version and location (if available)
	if kubectlPath, err := exec.LookPath("kubectl"); err == nil {
		env["kubectl_path"] = kubectlPath
		if output, err := exec.Command("kubectl", "version", "--client", "--short").Output(); err == nil {
			env["kubectl_version"] = strings.TrimSpace(string(output))
		}
	}

	// Podman version and location (if available)
	if podmanPath, err := exec.LookPath("podman"); err == nil {
		env["podman_path"] = podmanPath
		if output, err := exec.Command("podman", "version", "--format", "{{.Version}}").Output(); err == nil {
			env["podman_version"] = strings.TrimSpace(string(output))
		}
	}

	// Docker version and location (if available)
	if dockerPath, err := exec.LookPath("docker"); err == nil {
		env["docker_path"] = dockerPath
		if output, err := exec.Command("docker", "version", "--format", "{{.Server.Version}}").Output(); err == nil {
			env["docker_version"] = strings.TrimSpace(string(output))
		}
	}

	// Skewer (Python) location and version (if available)
	if skewerPath, err := exec.LookPath("skewer"); err == nil {
		env["skewer_path"] = skewerPath
		if output, err := exec.Command("skewer", "--version").Output(); err == nil {
			env["skewer_version"] = strings.TrimSpace(string(output))
		}
	}

	l.LogInfo("Environment", env)
}
