package executor

import (
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"sync"
	"syscall"

	"github.com/skupperproject/sketcher/internal/utils"
)

// ProcessTracker tracks background processes for cleanup
type ProcessTracker struct {
	processes []*exec.Cmd
	mu        sync.Mutex
}

var globalTracker = &ProcessTracker{}

// TrackProcess registers a background process for cleanup
func (pt *ProcessTracker) TrackProcess(cmd *exec.Cmd) {
	pt.mu.Lock()
	defer pt.mu.Unlock()
	pt.processes = append(pt.processes, cmd)
}

// CleanupAll kills all tracked processes
func (pt *ProcessTracker) CleanupAll() {
	pt.mu.Lock()
	defer pt.mu.Unlock()

	for _, cmd := range pt.processes {
		if cmd.Process != nil {
			utils.Debug("Killing background process (PID %d)", cmd.Process.Pid)
			cmd.Process.Kill()
		}
	}

	pt.processes = nil
}

// SetupSignalHandler sets up signal handling for cleanup
func SetupSignalHandler() {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-sigChan
		fmt.Fprintln(os.Stderr, "\nReceived interrupt, cleaning up...")
		CleanupBackgroundProcesses()
		os.Exit(130)
	}()
}

// CleanupBackgroundProcesses performs cleanup on exit
func CleanupBackgroundProcesses() {
	globalTracker.CleanupAll()

	// Also kill any kubectl port-forward processes we might have started
	// This catches processes started via shell with & that we don't track
	exec.Command("pkill", "-f", "kubectl port-forward").Run()
}

// RunBackgroundCommand runs a command in the background and tracks it
func RunBackgroundCommand(cmdStr string) error {
	cmd := exec.Command("sh", "-c", cmdStr)

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start background command: %w", err)
	}

	globalTracker.TrackProcess(cmd)
	utils.Debug("Started background process (PID %d): %s", cmd.Process.Pid, cmdStr)

	return nil
}
