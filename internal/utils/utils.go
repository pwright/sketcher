package utils

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"gopkg.in/yaml.v3"
)

// LogLevel represents logging verbosity
type LogLevel int

const (
	LogLevelDebug LogLevel = iota
	LogLevelInfo
	LogLevelWarn
	LogLevelError
)

var currentLogLevel = LogLevelInfo

// SetLogLevel sets the current log level
func SetLogLevel(level LogLevel) {
	currentLogLevel = level
}

// Color codes
const (
	colorReset  = "\033[0m"
	colorRed    = "\033[31m"
	colorGreen  = "\033[32m"
	colorYellow = "\033[33m"
	colorCyan   = "\033[36m"
)

func isColorEnabled() bool {
	return os.Getenv("SKETCHER_COLOR") != "" || isTerminal(os.Stdout)
}

func isTerminal(f *os.File) bool {
	stat, _ := f.Stat()
	return (stat.Mode() & os.ModeCharDevice) != 0
}

// Cprint prints with color
func Cprint(message, color string) {
	if isColorEnabled() {
		var code string
		switch color {
		case "red":
			code = colorRed
		case "green":
			code = colorGreen
		case "yellow":
			code = colorYellow
		case "cyan":
			code = colorCyan
		default:
			code = ""
		}
		fmt.Printf("%s%s%s\n", code, message, colorReset)
	} else {
		fmt.Println(message)
	}
}

// Debug logs a debug message
func Debug(message string, args ...interface{}) {
	if currentLogLevel <= LogLevelDebug {
		fmt.Printf(message+"\n", args...)
	}
}

// Info logs an info message
func Info(message string, args ...interface{}) {
	if currentLogLevel <= LogLevelInfo {
		fmt.Printf(message+"\n", args...)
	}
}

// Notice is an alias for Info
func Notice(message string, args ...interface{}) {
	Info(message, args...)
}

// Warn logs a warning message
func Warn(message string, args ...interface{}) {
	if currentLogLevel <= LogLevelWarn {
		fmt.Fprintf(os.Stderr, "Warning: "+message+"\n", args...)
	}
}

// Error logs an error message
func Error(message string, args ...interface{}) {
	if currentLogLevel <= LogLevelError {
		fmt.Fprintf(os.Stderr, "Error: "+message+"\n", args...)
	}
}

// ReadFile reads a file and returns its contents
func ReadFile(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// WriteFile writes content to a file
func WriteFile(path, content string) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(content), 0644)
}

// ReadYAML reads and parses a YAML file
func ReadYAML(path string, out interface{}) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(data, out)
}

// WriteYAML writes data to a YAML file
func WriteYAML(path string, data interface{}) error {
	content, err := yaml.Marshal(data)
	if err != nil {
		return err
	}
	return WriteFile(path, string(content))
}

// WriteYAMLToString converts data to YAML string
func WriteYAMLToString(data interface{}) (string, error) {
	content, err := yaml.Marshal(data)
	if err != nil {
		return "", err
	}
	return string(content), nil
}

// ReadJSON reads and parses a JSON file
func ReadJSON(path string, out interface{}) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, out)
}

// WriteJSON writes data to a JSON file
func WriteJSON(path string, data interface{}) error {
	content, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return WriteFile(path, string(content)+"\n")
}

// AbsolutePath returns the absolute path
func AbsolutePath(path string) (string, error) {
	return filepath.Abs(path)
}

// Exists checks if a path exists
func Exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// Run executes a command
func Run(command string, quiet bool) error {
	if !quiet {
		Notice("Running: %s", command)
	}

	cmd := exec.Command("sh", "-c", command)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// Call executes a command and returns stdout
func Call(command string, quiet bool) (string, error) {
	if !quiet {
		Notice("Running: %s", command)
	}

	cmd := exec.Command("sh", "-c", command)
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(string(output)), nil
}

// CheckProgram verifies a program is available
func CheckProgram(name string) error {
	if _, err := exec.LookPath(name); err != nil {
		return fmt.Errorf("required program '%s' is not available", name)
	}
	return nil
}

// AwaitPort waits for a port to be available
func AwaitPort(port int, host string, timeout int) error {
	start := time.Now()

	for {
		conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), time.Second)
		if err == nil {
			conn.Close()
			return nil
		}

		if time.Since(start) > time.Duration(timeout)*time.Second {
			return fmt.Errorf("timeout waiting for port %d on %s", port, host)
		}

		time.Sleep(5 * time.Second)
	}
}

// Base64Encode encodes data to base64
func Base64Encode(data string) string {
	return base64.StdEncoding.EncodeToString([]byte(data))
}

// Base64Decode decodes base64 data
func Base64Decode(data string) (string, error) {
	decoded, err := base64.StdEncoding.DecodeString(data)
	if err != nil {
		return "", err
	}
	return string(decoded), nil
}

// Capitalize capitalizes the first character only
func Capitalize(s string) string {
	if len(s) == 0 {
		return ""
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

// HTTPGet performs an HTTP GET request
func HTTPGet(url string, insecure bool, auth *struct{ User, Password string }) (string, error) {
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return "", err
	}

	if auth != nil {
		req.SetBasicAuth(auth.User, auth.Password)
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	return string(body), nil
}

// GetGitHubOwnerRepo extracts GitHub owner and repo from git remote origin URL
func GetGitHubOwnerRepo() (string, string, error) {
	url, err := Call("git remote get-url origin", true)
	if err != nil {
		return "", "", err
	}

	// SSH format: git@github.com:owner/repo.git
	if strings.HasPrefix(url, "git@github.com:") {
		path := strings.TrimPrefix(url, "git@github.com:")
		path = strings.TrimSuffix(path, ".git")
		parts := strings.SplitN(path, "/", 2)
		if len(parts) == 2 {
			return parts[0], parts[1], nil
		}
	}

	// HTTPS format: https://github.com/owner/repo.git
	if strings.HasPrefix(url, "https://github.com/") || strings.HasPrefix(url, "http://github.com/") {
		path := strings.TrimPrefix(url, "https://github.com/")
		path = strings.TrimPrefix(path, "http://github.com/")
		path = strings.TrimSuffix(path, ".git")
		parts := strings.SplitN(path, "/", 2)
		if len(parts) == 2 {
			return parts[0], parts[1], nil
		}
	}

	return "", "", fmt.Errorf("unknown git remote origin URL format: %s", url)
}

// IsProcessRunning checks if a process with the given PID is currently running.
// Returns true if the process exists and is running, false otherwise.
func IsProcessRunning(pid int) bool {
	if pid <= 0 {
		return false
	}

	process, err := os.FindProcess(pid)
	if err != nil {
		return false
	}

	// On Unix, FindProcess always succeeds, so send signal 0 to check
	// Signal 0 doesn't actually send a signal, just checks if we can
	err = process.Signal(syscall.Signal(0))
	return err == nil
}
