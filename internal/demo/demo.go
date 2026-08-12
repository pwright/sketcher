package demo

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/skupperproject/sketcher/internal/kubernetes"
	"github.com/skupperproject/sketcher/internal/model"
	"github.com/skupperproject/sketcher/internal/utils"
)

// Context represents demo context
type Context struct {
	Version   string                  `json:"version"`
	CreatedAt float64                 `json:"created_at"`
	PID       int                     `json:"pid"`
	WorkDir   string                  `json:"work_dir"`
	YAMLFile  string                  `json:"yaml_file"`
	Sites     map[string]*SiteContext `json:"sites"`
	DemoActive bool                   `json:"demo_active"`
}

// SiteContext represents site context
type SiteContext struct {
	Platform  string            `json:"platform"`
	Env       map[string]string `json:"env"`
	Namespace string            `json:"namespace,omitempty"`
	Title     string            `json:"title,omitempty"`
}

// CleanWorkDirIfNeeded removes the work directory if there's a stale demo context
// or if it's a different YAML file (different demo). Returns true if cleaned.
func CleanWorkDirIfNeeded(workDir, yamlFile string) (bool, error) {
	if workDir == "" {
		// Use /tmp directly to avoid macOS temp paths with special characters
		workDir = "/tmp/sketcher"
	}

	contextFile := filepath.Join(workDir, ".demo-context.json")

	// If no context file exists, work directory is clean
	if !utils.Exists(contextFile) {
		return false, nil
	}

	// Load existing context
	var context Context
	if err := utils.ReadJSON(contextFile, &context); err != nil {
		// Corrupted context - clean it
		fmt.Fprintf(os.Stderr, "Warning: Removing corrupted demo context\n")
		os.RemoveAll(workDir)
		return true, nil
	}

	// Check if process is still running
	if !utils.IsProcessRunning(context.PID) {
		fmt.Fprintf(os.Stderr, "Warning: Cleaning work directory from stale demo (PID %d no longer running)\n", context.PID)
		os.RemoveAll(workDir)
		return true, nil
	}

	// Check if it's a different YAML file (different demo)
	if context.YAMLFile != yamlFile {
		fmt.Fprintf(os.Stderr, "Warning: Active demo is for different file (%s vs %s), cleaning work directory\n", context.YAMLFile, yamlFile)
		os.RemoveAll(workDir)
		return true, nil
	}

	// Active demo for the same file - don't clean
	return false, nil
}

// LoadDemoContext loads demo context from state file
func LoadDemoContext(workDir string) (*Context, error) {
	if workDir == "" {
		// Use /tmp directly to avoid macOS temp paths with special characters
		workDir = "/tmp/sketcher"
	}

	contextFile := filepath.Join(workDir, ".demo-context.json")

	if !utils.Exists(contextFile) {
		return nil, fmt.Errorf("no active demo found")
	}

	var context Context
	if err := utils.ReadJSON(contextFile, &context); err != nil {
		return nil, err
	}

	// Check if process is still running
	if !utils.IsProcessRunning(context.PID) {
		fmt.Fprintf(os.Stderr, "Warning: Removing stale demo context (PID %d no longer running)\n", context.PID)
		os.Remove(contextFile) // Clean up stale context
		return nil, fmt.Errorf("no active demo found")
	}

	return &context, nil
}

// ValidateDemoContext validates demo context is usable
func ValidateDemoContext(context *Context) error {
	if context == nil {
		return fmt.Errorf("no active demo found. Run 'sketcher demo' first in another terminal")
	}

	if !context.DemoActive {
		return fmt.Errorf("demo process (PID %d) is no longer running. Please restart the demo", context.PID)
	}

	if context.WorkDir == "" || !utils.Exists(context.WorkDir) {
		return fmt.Errorf("demo work directory not found. Demo may have been cleaned up")
	}

	// Validate kubeconfigs exist
	for siteName, siteData := range context.Sites {
		if siteData.Platform == "kubernetes" {
			kubeconfig := siteData.Env["KUBECONFIG"]
			if kubeconfig != "" && !utils.Exists(kubeconfig) {
				return fmt.Errorf("kubeconfig for site '%s' not found: %s", siteName, kubeconfig)
			}
		}
	}

	return nil
}

// CreateExtendedModel creates a Model from saved context + extend file
func CreateExtendedModel(context *Context, extendFile string) (*model.Model, error) {
	if !utils.Exists(extendFile) {
		return nil, fmt.Errorf("extend file not found: %s", extendFile)
	}

	var extendData map[string]interface{}
	if err := utils.ReadYAML(extendFile, &extendData); err != nil {
		return nil, err
	}

	if extendData["steps"] == nil {
		return nil, fmt.Errorf("extend file '%s' must contain a 'steps' section", extendFile)
	}

	// Build synthetic skewer.yaml structure
	sitesData := make(map[string]interface{})
	for siteName, siteData := range context.Sites {
		siteMap := make(map[string]interface{})
		siteMap["platform"] = siteData.Platform
		if siteData.Namespace != "" {
			siteMap["namespace"] = siteData.Namespace
		}
		if siteData.Title != "" {
			siteMap["title"] = siteData.Title
		}

		envMap := make(map[string]interface{})
		for k, v := range siteData.Env {
			envMap[k] = v
		}
		siteMap["env"] = envMap

		sitesData[siteName] = siteMap
	}

	syntheticData := map[string]interface{}{
		"title": fmt.Sprintf("Extended Demo from %s", extendFile),
		"sites": sitesData,
		"steps": extendData["steps"],
	}

	// Write synthetic file
	syntheticFile := filepath.Join(context.WorkDir, ".extended-model.yaml")
	utils.Debug("Creating extended model file: %s", syntheticFile)
	if err := utils.WriteYAML(syntheticFile, syntheticData); err != nil {
		return nil, err
	}

	// Create model
	m, err := model.NewModel(syntheticFile, nil)
	if err != nil {
		return nil, err
	}

	// Override site env vars from context
	for _, site := range m.Sites {
		if siteContext, ok := context.Sites[site.Name]; ok {
			for k, v := range siteContext.Env {
				site.SetEnv(k, v)
			}
		}
	}

	if err := m.Check(); err != nil {
		return nil, err
	}

	return m, nil
}

// SaveDemoContext saves the demo context to a JSON file
func SaveDemoContext(m *model.Model, workDir string) error {
	contextFile := filepath.Join(workDir, ".demo-context.json")
	utils.Debug("Saving demo context to: %s", contextFile)

	// Extract site data from model
	sitesData := make(map[string]*SiteContext)
	for _, site := range m.Sites {
		siteData := &SiteContext{
			Platform: site.Platform,
			Env:      make(map[string]string),
		}

		for k, v := range site.Env {
			siteData.Env[k] = v
		}

		if site.Namespace != "" {
			siteData.Namespace = site.Namespace
		}

		if site.Title != "" {
			siteData.Title = site.Title
		}

		sitesData[site.Name] = siteData
	}

	context := &Context{
		Version:    "1.0",
		CreatedAt:  float64(time.Now().Unix()),
		PID:        os.Getpid(),
		WorkDir:    workDir,
		YAMLFile:   m.YAMLFile,
		Sites:      sitesData,
		DemoActive: true,
	}

	if err := utils.WriteJSON(contextFile, context); err != nil {
		return err
	}

	utils.Info("Demo context saved (PID %d)", context.PID)
	return nil
}

// PauseForDemo pauses and displays demo information to the user
func PauseForDemo(m *model.Model, quiet bool) error {
	utils.Notice("Pausing for demo time")

	var firstSite *model.Site
	if len(m.Sites) > 0 {
		firstSite = m.Sites[0]
	}

	var consoleURL string
	var password string
	var frontendURL string

	// Check for frontend and console (kubernetes only)
	if firstSite != nil && firstSite.Platform == "kubernetes" {
		err := firstSite.WithEnv(func() error {
			if kubernetes.ResourceExists("deployment/frontend") {
				frontendURL = "(See markdown for frontend URL)"
			}

			if kubernetes.ResourceExists("secret/skupper-console-users") {
				consoleHost, err := kubernetes.AwaitIngress("service/skupper", 300, quiet)
				if err == nil {
					consoleURL = fmt.Sprintf("https://%s:8010/", consoleHost)

					kubernetes.AwaitResource("secret/skupper-console-users", 30, quiet)
					passwordEncoded, err := kubernetes.GetResourceJSON("secret/skupper-console-users", ".data.admin")
					if err == nil {
						password, _ = utils.Base64Decode(strings.Trim(passwordEncoded, "'"))
					}
				}
			}

			return nil
		})

		if err != nil {
			return err
		}
	}

	// Display demo information
	fmt.Fprintln(os.Stderr)
	utils.Cprint("Demo time!", "cyan")
	fmt.Fprintln(os.Stderr)

	// Only show site configuration for kubernetes (where KUBECONFIG matters)
	hasKubernetes := false
	for _, site := range m.Sites {
		if site.Platform == "kubernetes" {
			hasKubernetes = true
			break
		}
	}

	if hasKubernetes {
		utils.Cprint("Sites:", "cyan")
		fmt.Fprintln(os.Stderr)

		for _, site := range m.Sites {
			if site.Platform == "kubernetes" {
				kubeconfig := site.Env["KUBECONFIG"]
				fmt.Fprintf(os.Stderr, "  %s: export KUBECONFIG=%s\n", site.Name, kubeconfig)
			}
		}

		fmt.Fprintln(os.Stderr)
	}

	if frontendURL != "" {
		utils.Cprint(fmt.Sprintf("Frontend URL:     %s", frontendURL), "green")
		fmt.Fprintln(os.Stderr)
	}

	if consoleURL != "" {
		utils.Cprint(fmt.Sprintf("Console URL:      %s", consoleURL), "green")
		fmt.Fprintln(os.Stderr, "Console user:     admin")
		utils.Cprint(fmt.Sprintf("Console password: %s", password), "yellow")
		fmt.Fprintln(os.Stderr)
	}

	// Wait for user (unless SKETCHER_DEMO_NO_WAIT is set)
	if os.Getenv("SKETCHER_DEMO_NO_WAIT") == "" {
		reader := bufio.NewReader(os.Stdin)
		for {
			fmt.Fprint(os.Stderr, "Are you done (yes)? ")
			response, err := reader.ReadString('\n')
			if err != nil {
				return err
			}

			if strings.TrimSpace(response) == "yes" {
				break
			}
		}
	}

	return nil
}
