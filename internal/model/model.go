package model

import (
	"fmt"
	"os"

	"github.com/skupperproject/sketcher/internal/utils"
)

// Model represents the top-level skewer.yaml structure
type Model struct {
	YAMLFile         string
	Data             map[string]interface{}
	Title            string
	Subtitle         string
	Workflow         string
	Overview         string
	Prerequisites    string
	Summary          string
	NextSteps        string
	AboutThisExample string
	Sites            []*Site
	Steps            []*Step
}

// Site represents a deployment site
type Site struct {
	Name      string
	Platform  string
	Namespace string
	Env       map[string]string
	Title     string
	Data      map[string]interface{}
}

// Step represents a workflow step
type Step struct {
	Number     int
	Numbered   bool
	Name       string
	Title      string
	Preamble   string
	Postamble  string
	Commands   map[string][]*Command
	Data       map[string]interface{}
}

// Command represents a command to execute
type Command struct {
	Run            string
	ExpectFailure  bool
	Apply          string
	Output         string
	AwaitResource  string
	AwaitIngress   string
	AwaitHTTPOK    []string
	AwaitConsoleOK bool
	AwaitPort      int
	Data           map[string]interface{}
}

// NewModel creates a new Model from a YAML file
func NewModel(yamlFile string, kubeconfigs []string) (*Model, error) {
	var data map[string]interface{}
	if err := utils.ReadYAML(yamlFile, &data); err != nil {
		return nil, err
	}

	model := &Model{
		YAMLFile: yamlFile,
		Data:     data,
	}

	// Apply kubeconfigs if provided
	if len(kubeconfigs) > 0 {
		if err := applyKubeconfigs(model, kubeconfigs); err != nil {
			return nil, err
		}
	}

	// Parse model
	if err := model.parse(); err != nil {
		return nil, err
	}

	return model, nil
}

func (m *Model) parse() error {
	// Parse text properties
	m.Title = getString(m.Data, "title")
	m.Subtitle = getString(m.Data, "subtitle")
	m.Workflow = getStringWithDefault(m.Data, "workflow", "main.yaml")
	m.Overview = getString(m.Data, "overview")
	m.Prerequisites = getString(m.Data, "prerequisites")
	m.Summary = getString(m.Data, "summary")
	m.NextSteps = getString(m.Data, "next_steps")
	m.AboutThisExample = getString(m.Data, "about_this_example")

	// Parse sites
	sitesData, ok := m.Data["sites"].(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid sites format")
	}

	for siteName, siteData := range sitesData {
		siteMap, ok := siteData.(map[string]interface{})
		if !ok {
			return fmt.Errorf("invalid site data for %s", siteName)
		}

		site := &Site{
			Name:     siteName,
			Platform: getString(siteMap, "platform"),
			Data:     siteMap,
		}

		if ns, ok := siteMap["namespace"].(string); ok {
			site.Namespace = ns
		}

		// Parse environment variables
		site.Env = make(map[string]string)
		if envData, ok := siteMap["env"].(map[string]interface{}); ok {
			for k, v := range envData {
				if str, ok := v.(string); ok {
					site.Env[k] = str
				}
			}
		}

		// Get title or capitalize name
		if title, ok := siteMap["title"].(string); ok {
			site.Title = title
		} else {
			site.Title = utils.Capitalize(siteName)
		}

		m.Sites = append(m.Sites, site)
	}

	// Parse steps
	stepsData, ok := m.Data["steps"].([]interface{})
	if !ok {
		return fmt.Errorf("invalid steps format")
	}

	for i, stepData := range stepsData {
		stepMap, ok := stepData.(map[string]interface{})
		if !ok {
			return fmt.Errorf("invalid step data")
		}

		step := &Step{
			Number:   i + 1,
			Numbered: getBoolWithDefault(stepMap, "numbered", true),
			Name:     getString(stepMap, "name"),
			Title:    getString(stepMap, "title"),
			Preamble: getString(stepMap, "preamble"),
			Postamble: getString(stepMap, "postamble"),
			Commands: make(map[string][]*Command),
			Data:     stepMap,
		}

		// Parse commands
		if commandsData, ok := stepMap["commands"].(map[string]interface{}); ok {
			for siteName, siteCommands := range commandsData {
				cmdList, ok := siteCommands.([]interface{})
				if !ok {
					return fmt.Errorf("invalid commands for site %s", siteName)
				}

				for _, cmdData := range cmdList {
					cmdMap, ok := cmdData.(map[string]interface{})
					if !ok {
						return fmt.Errorf("invalid command data")
					}

					cmd := &Command{
						Run:           getString(cmdMap, "run"),
						ExpectFailure: getBoolWithDefault(cmdMap, "expect_failure", false),
						Apply:         getString(cmdMap, "apply"),
						Output:        getString(cmdMap, "output"),
						AwaitResource: getString(cmdMap, "await_resource"),
						AwaitIngress:  getString(cmdMap, "await_ingress"),
						Data:          cmdMap,
					}

					// Parse await_port
					if port, ok := cmdMap["await_port"].(int); ok {
						cmd.AwaitPort = port
					}

					// Parse await_console_ok
					if _, ok := cmdMap["await_console_ok"]; ok {
						cmd.AwaitConsoleOK = true
					}

					// Parse await_http_ok
					if httpOK, ok := cmdMap["await_http_ok"].([]interface{}); ok {
						for _, v := range httpOK {
							if str, ok := v.(string); ok {
								cmd.AwaitHTTPOK = append(cmd.AwaitHTTPOK, str)
							}
						}
					}

					step.Commands[siteName] = append(step.Commands[siteName], cmd)
				}
			}
		}

		m.Steps = append(m.Steps, step)
	}

	return nil
}

// Check validates the model structure
func (m *Model) Check() error {
	if m.Title == "" {
		return fmt.Errorf("model missing required attribute 'title'")
	}

	for _, site := range m.Sites {
		if err := site.Check(); err != nil {
			return err
		}
	}

	for _, step := range m.Steps {
		if err := step.Check(m); err != nil {
			return err
		}
	}

	return nil
}

// Check validates a site configuration
func (s *Site) Check() error {
	if s.Platform == "" {
		return fmt.Errorf("site '%s' missing required attribute 'platform'", s.Name)
	}

	if s.Platform != "kubernetes" && s.Platform != "podman" {
		return fmt.Errorf("site '%s' has illegal platform value: %s", s.Name, s.Platform)
	}

	if s.Platform == "kubernetes" {
		if s.Namespace == "" {
			return fmt.Errorf("kubernetes site '%s' missing required attribute 'namespace'", s.Name)
		}

		if _, ok := s.Env["KUBECONFIG"]; !ok {
			return fmt.Errorf("kubernetes site '%s' has no KUBECONFIG environment variable", s.Name)
		}
	}

	if s.Platform == "podman" {
		platform, ok := s.Env["SKUPPER_PLATFORM"]
		if !ok {
			return fmt.Errorf("podman site '%s' has no SKUPPER_PLATFORM environment variable", s.Name)
		}

		if platform != "podman" && platform != "docker" && platform != "linux" {
			return fmt.Errorf("podman site '%s' environment variable SKUPPER_PLATFORM has illegal value: %s", s.Name, platform)
		}
	}

	return nil
}

// Check validates a step configuration
func (s *Step) Check(model *Model) error {
	if s.Title == "" {
		return fmt.Errorf("step %d missing required attribute 'title'", s.Number)
	}

	// Validate site names in commands
	siteNames := make(map[string]bool)
	for _, site := range model.Sites {
		siteNames[site.Name] = true
	}

	for siteName := range s.Commands {
		if !siteNames[siteName] {
			return fmt.Errorf("unknown site name '%s' in commands for step %d '%s'", siteName, s.Number, s.Title)
		}
	}

	return nil
}

// SetEnv sets an environment variable for the site
func (s *Site) SetEnv(key, value string) {
	s.Env[key] = value
	// Also update data map
	if s.Data["env"] == nil {
		s.Data["env"] = make(map[string]interface{})
	}
	envMap := s.Data["env"].(map[string]interface{})
	envMap[key] = value
}

// WithEnv returns a function that sets environment variables
func (s *Site) WithEnv(fn func() error) error {
	// Save current env
	oldEnv := make(map[string]string)
	for k, v := range s.Env {
		if oldVal, ok := os.LookupEnv(k); ok {
			oldEnv[k] = oldVal
		}
		os.Setenv(k, v)
	}

	// Restore on exit
	defer func() {
		for k := range s.Env {
			if oldVal, ok := oldEnv[k]; ok {
				os.Setenv(k, oldVal)
			} else {
				os.Unsetenv(k)
			}
		}
	}()

	return fn()
}

func applyKubeconfigs(model *Model, kubeconfigs []string) error {
	// Get kubernetes sites
	var kubeSites []*Site
	sitesData := model.Data["sites"].(map[string]interface{})

	for siteName, siteData := range sitesData {
		siteMap := siteData.(map[string]interface{})
		platform := getString(siteMap, "platform")

		if platform == "kubernetes" {
			kubeSites = append(kubeSites, &Site{
				Name: siteName,
				Data: siteMap,
			})
		}
	}

	if len(kubeconfigs) < len(kubeSites) {
		return fmt.Errorf("provided kubeconfigs (%d) are fewer than kubernetes sites (%d)", len(kubeconfigs), len(kubeSites))
	}

	for i, site := range kubeSites {
		if sitesData[site.Name] == nil {
			sitesData[site.Name] = make(map[string]interface{})
		}

		siteMap := sitesData[site.Name].(map[string]interface{})

		if siteMap["env"] == nil {
			siteMap["env"] = make(map[string]interface{})
		}

		envMap := siteMap["env"].(map[string]interface{})
		absPath, _ := utils.AbsolutePath(kubeconfigs[i])
		envMap["KUBECONFIG"] = absPath
	}

	return nil
}

func getString(m map[string]interface{}, key string) string {
	if v, ok := m[key].(string); ok {
		return v
	}
	return ""
}

func getStringWithDefault(m map[string]interface{}, key, def string) string {
	if v, ok := m[key].(string); ok {
		return v
	}
	return def
}

func getBoolWithDefault(m map[string]interface{}, key string, def bool) bool {
	if v, ok := m[key].(bool); ok {
		return v
	}
	return def
}
