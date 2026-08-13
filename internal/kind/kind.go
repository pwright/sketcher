package kind

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

// Kind manages a Kind cluster for testing
type Kind struct {
	YAMLFile    string
	Kubeconfigs []string
	WorkDir     string
	ClusterName string
	UseMetalLB  bool
}

// New creates a new Kind instance
func New(yamlFile string, useMetalLB bool) (*Kind, error) {
	return &Kind{
		YAMLFile:    yamlFile,
		// Use /tmp directly to avoid macOS temp paths with special characters
		WorkDir:     "/tmp/sketcher",
		ClusterName: "skewer",
		UseMetalLB:  useMetalLB,
	}, nil
}

// Setup starts Kind and creates kubeconfigs
func (k *Kind) Setup() error {
	fmt.Println("Starting Kind")

	if err := kubernetes.CheckEnvironment(); err != nil {
		return err
	}

	if err := utils.CheckProgram("kind"); err != nil {
		return err
	}

	// Check for existing cluster
	cmd := exec.Command("kind", "get", "clusters")
	output, _ := cmd.Output()
	clusters := strings.Split(strings.TrimSpace(string(output)), "\n")

	for _, cluster := range clusters {
		if cluster == k.ClusterName {
			return fmt.Errorf("a Kind cluster '%s' already exists. Delete it using 'kind delete cluster --name %s'", k.ClusterName, k.ClusterName)
		}
	}

	// Create work directory
	utils.Debug("Creating work directory: %s", k.WorkDir)
	if err := os.MkdirAll(k.WorkDir, 0755); err != nil {
		return err
	}

	// Create Kind config
	kindConfig := filepath.Join(k.WorkDir, "kind-config.yaml")
	utils.Debug("Creating Kind config file: %s", kindConfig)
	configContent := `kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  ipFamily: ipv4
  disableDefaultCNI: false
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    protocol: TCP
  - containerPort: 30443
    hostPort: 8443
    protocol: TCP
  - containerPort: 30010
    hostPort: 8010
    protocol: TCP
`
	if err := utils.WriteFile(kindConfig, configContent); err != nil {
		return err
	}

	// Create Kind cluster
	utils.Debug("Creating Kind cluster with name '%s'", k.ClusterName)
	if err := utils.Run(fmt.Sprintf("kind create cluster --name %s --config %s", k.ClusterName, kindConfig), false); err != nil {
		return err
	}

	// Load model to get sites
	m, err := model.NewModel(k.YAMLFile, nil)
	if err != nil {
		return err
	}

	if err := m.Check(); err != nil {
		return err
	}

	// Get Kind kubeconfig
	cmd = exec.Command("kind", "get", "kubeconfig", "--name", k.ClusterName)
	baseKubeconfig, err := cmd.Output()
	if err != nil {
		return err
	}

	// Generate kubeconfigs for kubernetes sites
	for _, site := range m.Sites {
		if site.Platform != "kubernetes" {
			continue
		}

		kubeconfigPath := site.Env["KUBECONFIG"]
		kubeconfigPath = filepath.Join(k.WorkDir, filepath.Base(kubeconfigPath))

		utils.Debug("Creating kubeconfig for site %s: %s", site.Name, kubeconfigPath)
		if err := utils.WriteFile(kubeconfigPath, string(baseKubeconfig)); err != nil {
			return err
		}

		utils.Debug("Setting KUBECONFIG for site %s: %s", site.Name, kubeconfigPath)
		site.SetEnv("KUBECONFIG", kubeconfigPath)
		k.Kubeconfigs = append(k.Kubeconfigs, kubeconfigPath)
	}

	// Install MetalLB if requested
	if k.UseMetalLB {
		if err := k.installMetalLB(); err != nil {
			return err
		}
	}

	return nil
}

// Cleanup stops Kind
func (k *Kind) Cleanup(debug bool) error {
	fmt.Println("Stopping Kind")

	// In debug mode, ask for confirmation before deleting cluster
	if debug {
		fmt.Printf("\nDelete Kind cluster '%s'? (y/n): ", k.ClusterName)
		var response string
		fmt.Scanln(&response)
		if response != "y" && response != "Y" {
			fmt.Println("Cluster preserved for inspection")
			return nil
		}
	}

	utils.Debug("Deleting Kind cluster '%s'", k.ClusterName)
	cmd := exec.Command("kind", "delete", "cluster", "--name", k.ClusterName)
	cmd.Run()

	return nil
}

// installMetalLB installs and configures MetalLB for LoadBalancer support
func (k *Kind) installMetalLB() error {
	utils.Info("Installing MetalLB for LoadBalancer support...")

	// Get the first kubeconfig
	if len(k.Kubeconfigs) == 0 {
		return fmt.Errorf("no kubeconfigs available")
	}
	kubeconfig := k.Kubeconfigs[0]

	// Install MetalLB using manifest
	utils.Debug("Applying MetalLB manifest")
	cmd := exec.Command("kubectl", "--kubeconfig", kubeconfig, "apply", "-f", "https://raw.githubusercontent.com/metallb/metallb/v0.14.5/config/manifests/metallb-native.yaml")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to install MetalLB: %w", err)
	}

	// Wait for MetalLB to be ready
	utils.Debug("Waiting for MetalLB controller to be ready")
	cmd = exec.Command("kubectl", "--kubeconfig", kubeconfig, "wait", "--namespace", "metallb-system",
		"--for=condition=ready", "pod", "--selector=app=metallb", "--timeout=90s")
	if err := cmd.Run(); err != nil {
		utils.Warn("MetalLB pods not ready yet, continuing anyway")
	}

	// Get Docker network subnet (IPv4 only)
	utils.Debug("Detecting Kind Docker network subnet")
	cmd = exec.Command("docker", "network", "inspect", "kind", "--format", "{{ range .IPAM.Config }}{{ if not (contains .Subnet \":\") }}{{ .Subnet }}{{ end }}{{ end }}")
	output, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("failed to get Docker network subnet: %w", err)
	}
	subnet := strings.TrimSpace(string(output))
	if subnet == "" {
		// Fallback: use default Docker bridge range
		subnet = "172.18.0.0/16"
		utils.Warn("No IPv4 subnet found in Kind network, using default: %s", subnet)
	}
	utils.Debug("Kind Docker subnet: %s", subnet)

	// Extract IP range from subnet (e.g., 172.18.0.0/16 -> 172.18.255.200-172.18.255.250)
	ipRange, err := k.calculateIPRange(subnet)
	if err != nil {
		return fmt.Errorf("failed to calculate IP range: %w", err)
	}
	utils.Info("MetalLB IP range: %s", ipRange)

	// Create IPAddressPool and L2Advertisement
	metalLBConfig := fmt.Sprintf(`apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: sketcher-pool
  namespace: metallb-system
spec:
  addresses:
  - %s
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: sketcher-advertisement
  namespace: metallb-system
spec:
  ipAddressPools:
  - sketcher-pool
`, ipRange)

	configPath := filepath.Join(k.WorkDir, "metallb-config.yaml")
	if err := utils.WriteFile(configPath, metalLBConfig); err != nil {
		return err
	}

	utils.Debug("Applying MetalLB configuration")
	cmd = exec.Command("kubectl", "--kubeconfig", kubeconfig, "apply", "-f", configPath)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to apply MetalLB configuration: %w", err)
	}

	utils.Info("MetalLB installed and configured successfully")
	return nil
}

// calculateIPRange calculates a safe IP range from a Docker subnet
func (k *Kind) calculateIPRange(subnet string) (string, error) {
	// Parse subnet (e.g., "172.18.0.0/16" or "192.168.207.0/24")
	parts := strings.Split(subnet, "/")
	if len(parts) != 2 {
		return "", fmt.Errorf("invalid subnet format: %s", subnet)
	}

	ip := parts[0]
	ipParts := strings.Split(ip, ".")
	if len(ipParts) != 4 {
		return "", fmt.Errorf("invalid IP format: %s", ip)
	}

	// Use the high end of the subnet for MetalLB (e.g., 172.18.255.200-172.18.255.250)
	// This avoids conflicts with existing Kind containers
	startIP := fmt.Sprintf("%s.%s.255.200", ipParts[0], ipParts[1])
	endIP := fmt.Sprintf("%s.%s.255.250", ipParts[0], ipParts[1])

	return fmt.Sprintf("%s-%s", startIP, endIP), nil
}
