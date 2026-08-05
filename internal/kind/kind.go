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
}

// New creates a new Kind instance
func New(yamlFile string) (*Kind, error) {
	return &Kind{
		YAMLFile:    yamlFile,
		WorkDir:     filepath.Join(os.TempDir(), "sketcher"),
		ClusterName: "skewer",
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
	if err := os.MkdirAll(k.WorkDir, 0755); err != nil {
		return err
	}

	// Create Kind config
	kindConfig := filepath.Join(k.WorkDir, "kind-config.yaml")
	configContent := `kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
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

		if err := utils.WriteFile(kubeconfigPath, string(baseKubeconfig)); err != nil {
			return err
		}

		site.SetEnv("KUBECONFIG", kubeconfigPath)
		k.Kubeconfigs = append(k.Kubeconfigs, kubeconfigPath)
	}

	return nil
}

// Cleanup stops Kind
func (k *Kind) Cleanup() error {
	fmt.Println("Stopping Kind")

	cmd := exec.Command("kind", "delete", "cluster", "--name", k.ClusterName)
	cmd.Run()

	return nil
}
