package minikube

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/skupperproject/sketcher/internal/kubernetes"
	"github.com/skupperproject/sketcher/internal/model"
	"github.com/skupperproject/sketcher/internal/utils"
)

// Minikube manages a Minikube cluster for testing
type Minikube struct {
	YAMLFile      string
	Kubeconfigs   []string
	WorkDir       string
	tunnelProcess *exec.Cmd
	tunnelOutput  *os.File
}

// New creates a new Minikube instance
func New(yamlFile string) (*Minikube, error) {
	return &Minikube{
		YAMLFile: yamlFile,
		// Use /tmp directly to avoid macOS temp paths with special characters
		WorkDir:  "/tmp/sketcher",
	}, nil
}

// Setup starts Minikube and creates kubeconfigs
func (mk *Minikube) Setup() error {
	fmt.Println("Starting Minikube")

	if err := kubernetes.CheckEnvironment(); err != nil {
		return err
	}

	if err := utils.CheckProgram("minikube"); err != nil {
		return err
	}

	// Create work directory
	utils.Debug("Creating work directory: %s", mk.WorkDir)
	if err := os.MkdirAll(mk.WorkDir, 0755); err != nil {
		return err
	}

	// Start Minikube
	utils.Debug("Starting minikube with profile 'skewer'")
	if err := utils.Run("minikube start -p skewer --auto-update-drivers false", false); err != nil {
		return err
	}

	// Start tunnel (background)
	tunnelOutputPath := filepath.Join(mk.WorkDir, "minikube-tunnel-output")
	utils.Debug("Creating tunnel output file: %s", tunnelOutputPath)
	tunnelOutput, err := os.Create(tunnelOutputPath)
	if err != nil {
		utils.Run("minikube delete -p skewer", false)
		return err
	}
	mk.tunnelOutput = tunnelOutput

	mk.tunnelProcess = exec.Command("minikube", "tunnel", "-p", "skewer")
	mk.tunnelProcess.Stdout = tunnelOutput
	mk.tunnelProcess.Stderr = tunnelOutput

	if err := mk.tunnelProcess.Start(); err != nil {
		tunnelOutput.Close()
		utils.Run("minikube delete -p skewer", false)
		return fmt.Errorf("failed to start minikube tunnel: %w", err)
	}

	utils.Notice("Started minikube tunnel (PID %d)", mk.tunnelProcess.Process.Pid)

	// Load model to get sites
	m, err := model.NewModel(mk.YAMLFile, nil)
	if err != nil {
		return err
	}

	if err := m.Check(); err != nil {
		return err
	}

	// Generate kubeconfigs for kubernetes sites
	for _, site := range m.Sites {
		if site.Platform != "kubernetes" {
			continue
		}

		kubeconfig := site.Env["KUBECONFIG"]
		// Expand ~ to work directory
		kubeconfig = strings.ReplaceAll(kubeconfig, "~", mk.WorkDir)
		kubeconfig = os.ExpandEnv(kubeconfig)

		// Make absolute if not already
		if !filepath.IsAbs(kubeconfig) {
			kubeconfig = filepath.Join(mk.WorkDir, kubeconfig)
		}

		utils.Debug("Setting KUBECONFIG for site %s: %s", site.Name, kubeconfig)
		site.SetEnv("KUBECONFIG", kubeconfig)
		mk.Kubeconfigs = append(mk.Kubeconfigs, kubeconfig)

		// Update context using site's environment
		utils.Debug("Updating minikube context for site %s (profile: skewer)", site.Name)
		err := site.WithEnv(func() error {
			cmd := exec.Command("minikube", "update-context", "-p", "skewer")
			return cmd.Run()
		})
		if err != nil {
			mk.Cleanup(false)
			return fmt.Errorf("failed to update context: %w", err)
		}

		// Verify kubeconfig was created
		if !utils.Exists(kubeconfig) {
			mk.Cleanup(false)
			return fmt.Errorf("kubeconfig not created: %s", kubeconfig)
		}
		utils.Debug("Kubeconfig verified: %s", kubeconfig)
	}

	return nil
}

// Cleanup stops Minikube
func (mk *Minikube) Cleanup(debug bool) error {
	fmt.Println("Stopping Minikube")

	// Stop tunnel
	if mk.tunnelProcess != nil {
		utils.Debug("Stopping minikube tunnel (PID %d)", mk.tunnelProcess.Process.Pid)
		mk.tunnelProcess.Process.Kill()
		mk.tunnelProcess.Wait() // Wait for process to exit
	}

	if mk.tunnelOutput != nil {
		mk.tunnelOutput.Close()
	}

	// In debug mode, ask for confirmation before deleting cluster
	if debug {
		fmt.Print("\nDelete minikube cluster 'skewer'? (y/n): ")
		var response string
		fmt.Scanln(&response)
		if response != "y" && response != "Y" {
			fmt.Println("Cluster preserved for inspection")
			return nil
		}
	}

	// Delete Minikube profile
	utils.Debug("Deleting minikube profile 'skewer'")
	cmd := exec.Command("minikube", "delete", "-p", "skewer")
	cmd.Run()

	return nil
}
